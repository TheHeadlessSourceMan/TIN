"""
Gather information by scanning a directory
"""
import typing
import os
import re
import json
from paths import LoadAndSave, URLCompatible, URL, asURL
from tin import IsMatchParam,MatchBase,asMatch


class DirectoriesSet(LoadAndSave):
    """
    A set of directories

    :yield: [description]
    :rtype: [type]
    """

    DEFAULT_IGNORE=['WINNT','node_modules','xinha','bin','lib','sbin',
        'emsdk','CordovaLib','pllatform_www','bllipparser',
        '.pytest_cache','AtdGrammarcheck','manuskript_x',
        '.metadata','.mypy_cache','cache']

    def __init__(self,
        directories:typing.Union[None,str,typing.Iterable[str]]=None,
        includeSubdirs:bool=True,
        ignore:typing.Optional[typing.Iterable[str]]=None,
        filename:typing.Optional[URLCompatible]=None):
        """ """
        LoadAndSave.__init__(self,filename)
        self._ignore:typing.Set[str]=set()
        self._isDefaultIgnore:bool=False
        if ignore is not None:
            self.ignore=ignore # type: ignore
        self._directories:typing.Set[str]=set()
        self._recursiveDirectories:typing.Set[str]=set()
        self.addDirectories(directories,includeSubdirs)

    @property
    def isDefaultIgnore(self)->bool:
        """
        Whether this is default ignore
        """
        return self._isDefaultIgnore

    @property
    def jsonObj(self)->typing.Any:
        """
        the directories set as a general Json object
        """
        ret:typing.Dict[str,typing.Any]={}
        if not self._isDefaultIgnore:
            ret['ignore']=[s for s in self._ignore]
        dirs:typing.List[typing.Dict[str,typing.Any]]=[]
        for d in self._directories:
            dirs.append({'d':d})
        for d in self._recursiveDirectories:
            dirs.append({'d':d,'recursive':'true'})
        ret['directories']=dirs
        return ret
    @jsonObj.setter
    def jsonObj(self,obj:typing.Dict):
        self.ignore=obj.get('ignore',None)
        self._directories=set()
        self._recursiveDirectories=set()
        for d in obj.get('directories',[]):
            if d.get('recursive',False):
                self._recursiveDirectories.add(d['d'])
            else:
                self._directories.add(d['d'])

    @property
    def json(self)->str:
        """
        Get the directories as a json string
        """
        return json.dumps(self.jsonObj)
    @json.setter
    def json(self,data:str):
        self.jsonObj=json.loads(data)

    def _decode(self,data:str)->None:
        """
        decode from plaintext
        """
        self.json=data

    def _encode(self)->str:
        """
        encode to plaintext
        """
        return self.json

    @property
    def ignore(self)->typing.Set[str]:
        """
        Directories to ignore
        """
        return self._ignore
    @ignore.setter
    def ignore(self,ignore:typing.Optional[typing.Iterable[str]]=None):
        self._isDefaultIgnore=ignore is None
        if ignore is None:
            ignore=self.DEFAULT_IGNORE
        self._ignore=set(ignore)

    def addDirectories(self,
        directories:typing.Union[None,str,typing.Iterable[str]],
        includeSubdirs:bool):
        """
        Add more directories to the set
        """
        if directories is None:
            return
        if isinstance(directories,str):
            self.add(directories,includeSubdirs)
        else:
            for d in directories:
                self.add(d,includeSubdirs)

    def add(self,dirname:str,includeSubdirs:bool)->None:
        """
        Add a directory to the list

        :param dirname: [description]
        :type dirname: [type]
        :param includeSubdirs: [description]
        :type includeSubdirs: [type]
        """
        # TODO: this could be made more clever, for instance
        # if dirname is recursive and another directory is
        # lower than that, etc.  For now KISS.
        if not os.path.isdir(dirname):
            if not os.path.isdir(dirname):
                print('ERR: directory "%s" is missing'%dirname)
            else:
                print('ERR: "%s" is not a directory'%dirname)
        if includeSubdirs:
            self._recursiveDirectories.add(dirname)
        else:
            self._directories.add(dirname)

    @property
    def allDirectories(self)->typing.Generator[URL,None,None]:
        """
        Iterates through all directories/subdirectories
        and returns a full path of each.

        NOTE:
            https://www.python.org/dev/peps/pep-0484/#annotating-generator-functions-and-coroutines
        NOTE: has recursion protection built in
        """
        ignore=set()
        def r(dd:str)->typing.Generator[URL,None,None]:
            if dd in ignore:
                return
            ignore.add(dd)
            yield asURL(dd)
            for d in os.listdir(dd):
                if d in self.ignore:
                    continue
                d='%s%s%s'%(dd,os.sep,d)
                if os.path.isdir(d):
                    yield from r(d)
        for d in self._recursiveDirectories:
            yield from r(os.path.abspath(d))
        # do the simple dirs last
        # just in case they were already found by recursion
        for d in self._directories:
            if d in self.ignore:
                continue
            d=os.path.abspath(d)
            if d in ignore:
                continue
            ignore.add(d)
            yield asURL(d)

    def _checkDirectory(self,
        d:URL,
        cleanMatches:typing.List[typing.Union[
            MatchBase,
            typing.Tuple[MatchBase,MatchBase]]]
        )->bool:
        """
        check to see if a single directory matches true
        against a clean set of matches
        """
        filenames=d.children
        for m in cleanMatches:
            if isinstance(m,tuple):
                for f in filenames:
                    if m[0].matches(f):
                        filename="%s%s%s"%(d,os.sep,f)
                        data=open(filename,'rb').read().decode('utf-8')
                        if m[0].matches(data):
                            return True
            else:
                for f in filenames:
                    if m.matches(f):
                        return True
        return False

    def directoriesContaining(self,
        matching:typing.Union[
            IsMatchParam,
            typing.Tuple[IsMatchParam,IsMatchParam],
            typing.Iterable[typing.Union[
                IsMatchParam,
                typing.Tuple[IsMatchParam,IsMatchParam]]]
        ]):
        """
        Search given a set of search parameters and yield the directory names

        If matching can be:
            a filename - anything IsMatchParam supports
            a (filename,fileContents) - each as anything IsMatchParam supports
            or any mixed iterable of these things,
            wherein only one entry has to match

        NOTE: if a tuple of exactly 2 items, it is always assumed to be
            (filenameMatch,fileContentsMath)
            but if an array of 2 items is given, it is assumed to be
            [filenameMatch,filenameMatch]
            therefore:
              PREFER LISTS FOR FILENAME LISTS AND TUPLES FOR FILENAME+CONTENTS
        """
        # massage input so it is ALWAYS an iterable of
        # MatchBase or (MatchBase,MatchBase)
        cleanMatches:typing.List[typing.Union[
            MatchBase,
            typing.Tuple[MatchBase,MatchBase]]]=[]
        if matching is None:
            return
        elif isinstance(matching,(str,MatchBase,re.Pattern)):
            cleanMatches=[asMatch(matching)]
        elif isinstance(matching,tuple) and len(matching)==2:
            cleanMatches=[(asMatch(matching[0]),asMatch(matching[1]))]
        else:
            for m in matching:
                if isinstance(m,tuple):
                    if len(m)<2:
                        continue
                    m=(asMatch(m[0]),asMatch(m[1]))
                else:
                    m=asMatch(m)
                cleanMatches.append(m)
        # now do the search
        for d in self.allDirectories:
            if self._checkDirectory(d,cleanMatches):
                yield d


class DirectoriesSearch(DirectoriesSet):
    """
    a DirectoriesSet coupled with search parameters.

    By bundling the two together we can achieve pre-defined searches
    which we can serialize/deserialize to json
    """

    def __init__(self,name:str,
        matching:typing.Union[
            IsMatchParam,
            typing.Tuple[IsMatchParam,IsMatchParam],
            typing.Iterable[typing.Union[
                str,
                typing.Tuple[IsMatchParam,IsMatchParam]]]],
        directories:typing.Union[None,str,typing.Iterable[str]]=None,
        includeSubdirs:bool=True,
        ignore:typing.Optional[typing.List[str]]=None):
        """ """
        DirectoriesSet.__init__(self,directories,includeSubdirs,ignore)
        self._matching:typing.Union[
            IsMatchParam,
            typing.Tuple[IsMatchParam,IsMatchParam],
            typing.Iterable[typing.Union[str,typing.Tuple[
                IsMatchParam,
                IsMatchParam]]]]=matching
        self._results:typing.Optional[typing.List[str]]=None
        self.name:str=name

    @property
    def matching(self):
        """
        Return matching items
        """
        return self._matching
    @matching.setter
    def matching(self,matching):
        self._matching=matching
        self._results=[]

    def reload(self)->typing.List[str]:
        """
        force a reload
        """
        self._results=[r for r in self.directoriesContaining(self.matching)]
        return self._results

    @property
    def jsonObj(self)->typing.Dict:
        """
        the search critera as a json-compatible object
        """
        ret=DirectoriesSet.__dict__['jsonObj'].fget(self)
        ret['matching']=self.matching
        print(ret.items())
        return ret
    @jsonObj.setter
    def jsonObj(self,obj:typing.Dict):
        DirectoriesSet.jsonObj(self)
        self.matching=obj['matching']

    @property
    def results(self):
        """
        gets cached results, or automatically searches if necessary

        if you always want to re-search, use reload()
        """
        if self._results is None:
            self._results=self.reload()
        return self._results

    def __getitem__(self,idx:typing.Union[int,typing.Tuple[int,int]]):
        return self.results[idx]

    def __len__(self)->int:
        return len(self.results)

    def __iter__(self)->typing.Iterable:
        """
        loop through the found values

        NOTE: since we don't know whether all results were visited, this
        will not cache.  In cases where you may want to run more than once
        it may be more efficient to use .results
        """
        if self._results is not None:
            return self._results.__iter__()
        else:
            return self.directoriesContaining(self.matching)

    def __str__(self)->str:
        ret=[self.name]
        ret.extend(self.results)
        return '\n  '.join(ret)


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        ds=DirectoriesSet(r"c:\backed_up")
        didSomething=False
        for arg in args:
            if arg.startswith('-'):
                av=[a.strip() for a in arg.split('=',1)]
                if av[0] in ['-h','--help']:
                    printhelp=True
                elif av[0]=='--git':
                    didSomething=True
                    print('git projects:')
                    for d in ds.directoriesContaining(".git"):
                        print('   %s'%d)
                elif av[0]=='--projecto':
                    print('projecto projects:')
                    reg=re.compile(r"""project\.[x]?htm[l]?""")
                    for d in ds.directoriesContaining(reg):
                        print('   %s'%d)
                elif av[0]=='--save':
                    didSomething=True
                    ds.save(av[1])
                elif av[0]=='--load':
                    ds.load(av[1])
                else:
                    print('ERR: unknown argument "'+av[0]+'"')
            else:
                ds.load(arg)
        if not didSomething:
            print('WARN: Did not do anything.')
            printhelp=True
    if printhelp:
        print('Usage:')
        print('   gather.py [options] [filename.json]')
        print('Options:')
        print('   --help ............ this help')
        print('   --git ............. sample to locate all git projects')
        print('   --projecto ........ sample to locate all projecto projects')
        print('   --save[=filename] . save the config file')
        print('   --load[=filename] . load the config file')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
