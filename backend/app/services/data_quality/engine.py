from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol
import pandas as pd

class QualitySeverity(str, Enum):
    INFO="INFO"; WARNING="WARNING"; ERROR="ERROR"; CRITICAL="CRITICAL"

@dataclass(frozen=True)
class QualityIssue:
    rule_name:str
    dataset:str
    severity:QualitySeverity
    message:str
    affected_rows:int=0
    column:str|None=None
    metadata:dict[str,Any]|None=None

@dataclass(frozen=True)
class QualityRuleResult:
    rule_name:str
    passed:bool
    issues:tuple[QualityIssue,...]=()
    @property
    def issue_count(self)->int: return len(self.issues)

@dataclass(frozen=True)
class DatasetQualityReport:
    dataset:str
    row_count:int
    column_count:int
    results:tuple[QualityRuleResult,...]
    @property
    def issues(self): return tuple(i for r in self.results for i in r.issues)
    @property
    def passed_rules(self): return sum(r.passed for r in self.results)
    @property
    def failed_rules(self): return sum(not r.passed for r in self.results)
    @property
    def issue_count(self): return len(self.issues)

class QualityRule(Protocol):
    name:str
    def evaluate(self,dataframe:pd.DataFrame,dataset:str)->QualityRuleResult: ...

class QualityRuleRegistry:
    def __init__(self): self._rules={}
    def register(self,rule):
        if rule.name in self._rules: raise ValueError(f"Quality rule already registered: {rule.name}")
        self._rules[rule.name]=rule
    def get(self,name):
        if name not in self._rules: raise KeyError(f"Quality rule not registered: {name}")
        return self._rules[name]
    def all(self): return tuple(self._rules.values())
    def __len__(self): return len(self._rules)

class DataQualityEngine:
    def __init__(self,registry=None): self.registry=registry or QualityRuleRegistry()
    def register(self,rule): self.registry.register(rule)
    def run(self,dataframe,dataset):
        results=tuple(r.evaluate(dataframe,dataset) for r in self.registry.all())
        return DatasetQualityReport(dataset,len(dataframe),len(dataframe.columns),results)
