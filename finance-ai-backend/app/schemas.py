from pydantic import BaseModel

class FraudResponse(BaseModel):

    riskScore:int

    riskLevel:str

    title:str

    summary:str

    recommendation:str

    reasons:list[str]

    actions:list[str]