"""
TIN means Todos, Ideas, and Notes files.

There is an expansion called TINS which adds Shopping
"""
import os
import typing
import re
import subprocess
from paths import URLCompatible,Url
import tin


# TODO: should accept projecto projects too??
#    Or is this a subset of projecto??
ACCEPTABLE_EXTENSIONS=['txt','htm','html','md']


class Tin:
    """
    TIN means Todos, Ideas, and Notes files.

    There is an expansion called TINS which adds Shopping
    """

    def __init__(self,directory:URLCompatible):
        """
        represents a single Tin directory
        """
        directory=Url(directory)
        self.name:str=directory[-1]
        self.directory:Url=directory
        self._fileContents:typing.Dict[Url,str]={}

    def _findFileInDir(self,
        filenamesWithoutExt:typing.Union[str,typing.Iterable[str]]
        )->typing.Optional[Url]:
        """
        Find a file of a given name in the directory
        """
        if isinstance(filenamesWithoutExt,str):
            filenamesWithoutExt=[filenamesWithoutExt]
        filenames=os.listdir(self.directory.filePath)
        for filenameWithoutExt in filenamesWithoutExt:
            for ext in ACCEPTABLE_EXTENSIONS:
                filename='%s.%s'%(filenameWithoutExt,ext)
                if filename in filenames:
                    return Url(filename)
        return None

    def _findHeading(self,text:typing.Optional[str],heading:str)->int:
        """
        returns the line number where the heading is located,
        or -1 if not found
        """
        if text is None:
            return -1
        lastLine=''
        heading=heading.strip().lower()
        for i,line in enumerate(text.split('\n')):
            line=line.strip()
            if line:
                if line[-1]==':':
                    if line.lower()==heading:
                        return i
                if line.startswith('---') or line.startswith('==='):
                    # it's a separator, so the previous line could be a heading
                    if lastLine.lower()==heading:
                        return i
            lastLine=line
        return -1

    def tinFilename(self,tinName:str)->typing.Optional[Url]:
        """
        get a filname for the base file
        """
        tinName=tinName.split('.',1)[0]
        if tinName.endswith('s'):
            alt=tinName+'s'
        else:
            alt=tinName[0:-1]
        return self._findFileInDir([tinName,alt])

    def openTin(self,tinName:str):
        """
        open current file or create a new one
        """
        filename:typing.Optional[Url]=self.tinFilename(tinName)
        if filename is None:
            filename=Url(tinName+'.txt')
        cmd='start /b '
        filename=self.directory+filename
        ccmd='%s "%s"'%(cmd,filename)
        print(ccmd)
        subprocess.Popen(ccmd,shell=True).communicate()

    @property
    def todoFilename(self)->typing.Optional[Url]:
        """
        Get the filename of the todo file.
        """
        return self.tinFilename('todo')
    @property
    def ideasFilename(self)->typing.Optional[Url]:
        """
        Get the filename of the ideas file.
        """
        return self.tinFilename('ideas')
    @property
    def notesFilename(self)->typing.Optional[Url]:
        """
        Get the filename of the notes file.
        """
        return self.tinFilename('notes')
    @property
    def shoppingFilename(self)->typing.Optional[Url]:
        """
        Get the filename of the shpping file.
        """
        return self.tinFilename('shopping')

    def openTodo(self):
        """
        open using the default system editor
        """
        self.openTin('todo')

    def openIdeas(self):
        """
        open using the default system editor
        """
        self.openTin('ideas')

    def openNotes(self):
        """
        open using the default system editor
        """
        self.openTin('notes')

    def openShopping(self):
        """
        open using the default system editor
        """
        self.openTin('shopping')

    def getTinData(self,tinName:str)->typing.Optional[str]:
        """
        also caches.
        """
        filename=self.tinFilename(tinName)
        if filename is None:
            return None
        if filename in self._fileContents:
            return self._fileContents[filename]
        data=filename.read()
        self._fileContents[filename]=data
        return data

    @property
    def todo(self)->typing.Optional[str]:
        """
        Get todo data
        """
        return self.getTinData('todo')
    @property
    def ideas(self)->typing.Optional[str]:
        """
        Get ideas data
        """
        return self.getTinData('ideas')
    @property
    def notes(self)->typing.Optional[str]:
        """
        Get notes data
        """
        return self.getTinData('notes')
    @property
    def shopping(self)->typing.Optional[str]:
        """
        Get shopping data
        """
        return self.getTinData('shopping')

    def __str__(self):
        ret=[self.name]
        for tinName in ('todo','ideas','notes'):
            filename=self.tinFilename(tinName)
            if filename is not None:
                ret.append('%s: %s'%(tinName,filename))
        return '\n   '.join(ret)


class TinFinder:
    """
    TIN = Todo's, Ideas, Notes
    the idea is to gather up all directories with text files like these,
    and then ultimately be able to flip through and view/edit them as part of
    a project management strategy
    """

    def __init__(self,
        searchDirectories:typing.Union[str,typing.Iterable[str]]):
        """ """
        if isinstance(searchDirectories,str):
            searchDirectories=[searchDirectories]
        extensions:typing.Set[str]=set(ACCEPTABLE_EXTENSIONS)
        filenames:typing.List[str]=['todo','todos','ideas','notes']
        extensionsRe:str='(\\.(%s))'%('|'.join(extensions))
        filenamesRe:str='(%s)'%('|'.join(filenames))
        matching:typing.Pattern=re.compile(
            filenamesRe+extensionsRe,re.IGNORECASE)
        self._directorySearch:tin.DirectoriesSearch= \
            tin.DirectoriesSearch('TIN',matching,searchDirectories,True,None)
        self._projects:typing.Optional[typing.Dict[str,Tin]]=None

    def reload(self)->typing.Dict[str,Tin]:
        """
        Reload all projects and return the list

        :return: all known projects
        :rtype: typing.Dict[str,Tin]
        """
        self._projects={}
        for r in self._directorySearch.reload():
            tin=Tin(r)
            self._projects[tin.name]=tin
        return self._projects

    def edit(self,project:str,tinName:str):
        """
        Open the file type in the system editor
        """
        proj:typing.Optional[Tin]=self.projects.get(project)
        if proj is None:
            raise Exception('No project by that name')
        proj.openTin(tinName)

    def load(self,filename:typing.Optional[URLCompatible]=None)->None:
        """
        load a series of projects
        """
        self._directorySearch.load(filename)

    def save(self,filename:typing.Optional[URLCompatible]=None)->None:
        """
        save a series of projects
        """
        self._directorySearch.save(filename)

    @property
    def results(self)->typing.Iterable[Tin]:
        """
        automatically loads if necessary
        """
        return self.projects.values()

    @property
    def projects(self)->typing.Dict[str,Tin]:
        """
        All of the current projects
        """
        if self._projects is None:
            self._projects=self.reload()
        return self._projects

    def __iter__(self):
        return self.projects.__iter__

    def __getitem__(self,idx):
        if isinstance(idx,str):
            return self.projects[idx]
        return self.results.__getitem__(idx)

    def __len__(self):
        return len(self.projects)

    def __str__(self):
        return '\n'.join([str(s) for s in self.results])


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        t=TinFinder('c:\\backed_up')
        didSomething=False
        for arg in args:
            if arg.startswith('-'):
                av=[a.strip() for a in arg.split('=',1)]
                if av[0] in ['-h','--help']:
                    printhelp=True
                elif av[0]=='--all':
                    didSomething=True
                    print(t)
                elif av[0]=='--edit':
                    didSomething=True
                    nameTin=av[1].split('/')
                    t.edit(nameTin[0],nameTin[1])
                elif av[0]=='--save':
                    didSomething=True
                    t.save(av[1])
                elif av[0]=='--load':
                    t.load(av[1])
                else:
                    print('ERR: unknown argument "'+av[0]+'"')
            else:
                t.load(arg)
        if not didSomething:
            print('WARN: Did not do anything.')
            printhelp=True
    if printhelp:
        print('Usage:')
        print('   tin.py [options] [filename.json]')
        print('Options:')
        print('   --help ............ this help')
        print('   --all ............. print all items')
        print('   --edit[=name/tin] . edit the particular file eg --edit=myproj/todo')
        print('   --save[=filename] . save the config file')
        print('   --load[=filename] . load the config file')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
