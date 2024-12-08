"""
base class for searches

can build up like
    Match(and=(Match(("this","or this")),Match("but always this")))
"""
import typing
from abc import abstractmethod


IsMatchable=typing.Union[str,'MatchBase',typing.Pattern]
IsMatchParam=typing.Union[None,IsMatchable,typing.Iterable[IsMatchable]]
def asMatch(m:IsMatchParam)->'MatchBase':
    """
    Always returns a MatchBase.

    If m is already a MatchBase, will not create a new one.

    :param m: [description]
    :type m: IsMatchParam
    :return: [description]
    :rtype: [type]
    :yield: [description]
    :rtype: [type]
    """
    if isinstance(m,MatchBase):
        return m
    return Match(m)

class MatchBase:
    """
    Base class for all matchers
    """

    def __call__(self,x:str)->bool:
        """
        calling this object like a method is the same as matches()
        """
        return self.matches(x)

    @abstractmethod
    def matches(self,x:str)->bool:
        """
        check to see if the string x matches our criteria

        :param x: [description]
        :type x: str
        :return: [description]
        :rtype: bool
        """


class Match(MatchBase):
    """
    base class for searches

    can build up like:
    Match(and=(Match(("this","or this")),Match("but always this")))
    """

    def __init__(self,
        anyOf:IsMatchParam=None,
        allOf:IsMatchParam=None,
        noneOf:IsMatchParam=None):
        """
        NOTE: if anyOf and allOf are both used, implies an or situation
            eg Match(anyOf=x,allOf=y)
            is the same as Match(anyOf=[x,Match(allOf=y)])
        NOTE: if noneOf is preset, it always overrules everything else
        NOTE: if nothing at all is specified, always returns False
        """
        self.assign(anyOf,allOf,noneOf)

    def assign(self,
        anyOf:IsMatchParam=None,
        allOf:IsMatchParam=None,
        noneOf:IsMatchParam=None):
        """
        Assign the value of this match

        NOTE: if anyOf and allOf are both used, implies an or situation
            eg Match(anyOf=x,allOf=y)
            is the same as Match(anyOf=[x,Match(allOf=y)])
        NOTE: if noneOf is preset, it always overrules everything else
        NOTE: if nothing at all is specified, always returns False
        """
        self.anyOf:typing.List[IsMatchable]=[]
        self.allOf:typing.List[IsMatchable]=[]
        self.noneOf:typing.List[IsMatchable]=[]
        self.append(anyOf,allOf,noneOf)

    def append(self,anyOf,allOf,noneOf):
        """
        Add more match criteria
        """
        if anyOf is not None:
            self.anyOf.append(anyOf)
        if allOf is not None:
            self.anyOf.append(allOf)
        if noneOf is not None:
            self.anyOf.append(noneOf)

    def _matchItem(self,m:IsMatchable,x:str):
        """
        match a single matchable item

        :param m: [description]
        :type m: IsMatchable
        :param x: [description]
        :type x: str
        """
        if isinstance(m,str):
            return m==x
        if isinstance(m,MatchBase):
            return m(x)
        # must be a regex
        return m.match(x) is not None

    def matches(self,x:str)->bool:
        """
        check to see if the string x matches our criteria

        :param x: [description]
        :type x: str
        :return: [description]
        :rtype: bool
        """
        defaultReturn=False
        for m in self.noneOf:
            if self._matchItem(m,x):
                return False
            defaultReturn=True
        for m in self.anyOf:
            if self._matchItem(m,x):
                return True
            defaultReturn=False
        for m in self.allOf:
            if not self._matchItem(m,x):
                return False
            defaultReturn=True
        return defaultReturn
