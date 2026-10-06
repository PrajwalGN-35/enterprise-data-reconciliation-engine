import pandas as pd
import pytest
from app.services.data_quality import DataQualityEngine, QualityIssue, QualityRuleRegistry, QualityRuleResult, QualitySeverity

class PassRule:
    name="pass_rule"
    def evaluate(self,dataframe,dataset): return QualityRuleResult(self.name,True)

class FailRule:
    name="fail_rule"
    def evaluate(self,dataframe,dataset):
        issue=QualityIssue(self.name,dataset,QualitySeverity.ERROR,"Test failure",2,"amount")
        return QualityRuleResult(self.name,False,(issue,))

def test_registry():
    r=QualityRuleRegistry(); r.register(PassRule()); r.register(FailRule())
    assert [x.name for x in r.all()]==["pass_rule","fail_rule"]
    with pytest.raises(ValueError): r.register(PassRule())

def test_engine_report():
    df=pd.DataFrame({"id":[1,2,3],"amount":[100,200,300]})
    e=DataQualityEngine(); e.register(PassRule()); e.register(FailRule())
    report=e.run(df,"customers")
    assert (report.dataset,report.row_count,report.column_count)==("customers",3,2)
    assert report.passed_rules==1 and report.failed_rules==1 and report.issue_count==1
    assert report.issues[0].severity is QualitySeverity.ERROR

def test_empty_engine():
    report=DataQualityEngine().run(pd.DataFrame(columns=["id"]),"empty")
    assert report.row_count==0 and report.column_count==1 and report.results==()
