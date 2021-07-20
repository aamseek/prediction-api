import numpy as np
import pandas as pd
import pickle
from datetime import datetime

# load model
model = pickle.load(open('model.pkl','rb'))

def main(result):

    # response_list = query_result.get('borrower', {}).get('lenderApprovalObject',{}).get('dmi',{}).get('readyForDecisionResponse',{}).get('multibureauData',{}).get('FINISHED')
    if result:
        approval_object = result.get('borrower', {}).get('lenderApprovalObject')
    else:
        approval_object = None

    if type(approval_object) is dict:
        response = approval_object.get('dmi',{}).get('readyForDecisionResponse',{}).get('multibureauData',{}).get('FINISHED')
    else:
        response = None

    # credit_report = query_result['borrower']['lenderApprovalObject']['dmi']['readyForDecisionResponse']['multibureauData']['FINISHED'][0]['JSON-RESPONSE-OBJECT']

    column_list = ["prev_income","accounts","enquiry","age","other_loan_max","autop_loan_max","housing_loan_max","property_loan_max","personal_loan_max","consumer_loan_max","gold_loan_max","credit_card_max","overdraft_max","twowheeler_loan_max","commercialvehicle_loan_max","loan_total_total","loan_max_max","emi_total_total","emi_max_max","employment_type","gender","f1"]
    df = pd.DataFrame(columns=column_list)
    df.loc[0] = 0
    df['dob'] = ''

    if result:
        df.at[0,'employment_type'] = result.get('borrower', {}).get('work',{}).get('employment_type')
        df.at[0,'gender'] = result.get('borrower', {}).get('gender')
        df.at[0,'dob'] = result.get('borrower', {}).get('dob')

    if response:
        accounts = response[0].get('JSON-RESPONSE-OBJECT',{}).get('accountList')
        enquiry = response[0].get('JSON-RESPONSE-OBJECT',{}).get('enquiryList')
        employment = response[0].get('JSON-RESPONSE-OBJECT',{}).get('employmentList')

    else:
        accounts = []
        enquiry = []
        employment = []

    if employment:
        if employment[0].get("monthlyAnnuallyIndicator") == 'M':
            prev_income = int(employment[0].get('income',"0"))
        elif employment[0].get("monthlyAnnuallyIndicator") == 'A' or int(employment[0].get('income',"0")) >= 180000:
            prev_income = int(employment[0].get('income',"0")) / 12
        else:
            prev_income = int(employment[0].get('income',"0"))
    else:
        prev_income = 0

    df.at[0,'prev_income'] = prev_income

    if enquiry:
        df.at[0,'enquiry'] = len(enquiry)
    else:
        df.at[0,'enquiry'] = 0

    if accounts:
        df.at[0,'accounts'] = len(accounts)
    else:
        df.at[0,'accounts'] = 0

    for item in accounts or []:
      if item['accountType'] == '00':
        df.at[0,'other_loan_max'] = max(df.at[0,'other_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '01':
        df.at[0,'autop_loan_max'] = max(df.at[0,'autop_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '02':
        df.at[0,'housing_loan_max'] = max(df.at[0,'housing_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '03':
        df.at[0,'property_loan_max'] = max(df.at[0,'property_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '05':
        df.at[0,'personal_loan_max'] = max(df.at[0,'personal_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '06':
        df.at[0,'consumer_loan_max'] = max(df.at[0,'consumer_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '07':
        df.at[0,'gold_loan_max'] = max(df.at[0,'gold_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '10':
        df.at[0,'credit_card_max'] = max(df.at[0,'credit_card_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '12':
        df.at[0,'overdraft_max'] = max(df.at[0,'overdraft_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '13':
        df.at[0,'twowheeler_loan_max'] = max(df.at[0,'twowheeler_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      if item['accountType'] == '17':
        df.at[0,'commercialvehicle_loan_max'] = max(df.at[0,'commercialvehicle_loan_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      df.at[0,'loan_total_total'] += float(item.get('highCreditOrSanctionedAmount',"0"))
      df.at[0,'loan_max_max'] = max(df.at[0,'loan_max_max'],float(item.get('highCreditOrSanctionedAmount',"0")))
      df.at[0,'emi_total_total'] += float(item.get('emiAmount',"0"))
      df.at[0,'emi_max_max'] = max(df.at[0,'emi_max_max'],float(item.get('emiAmount',"0")))

    dob = df.at[0,'dob']
    today = datetime.today()

    if dob and len(dob)>4:
        df['age'] = today.year- int(dob[:4])
    df.drop('dob',axis=1,inplace=True)

    df['gender'] = np.where(df['gender'] == "female", 1, 0)
    df['employment_type'] = np.where(df['employment_type'] == "Salaried", 0, 1)
    df['f1'] = df['age']*df['credit_card_max']

    # print(df.columns)
    # print(df.loc[0])
    predicted= model.predict(df)

    if response is None:
        income_cat = "BNF"
        predicted_income = "BNF"
    elif accounts is None:
        income_cat = "NA"
        predicted_income = "NA"
    elif predicted > 24000:
        income_cat = ">20k"
        predicted_income = round(predicted[0],2)
    else:
        income_cat = "<20k"
        predicted_income = round(predicted[0],2)

    enquiry_count = 0
    today = datetime.today()
    for item in enquiry or []:
      enquiry_date = item.get('dateReported')
      datetime_object = datetime.strptime(enquiry_date, '%d%m%Y')
      if float(item.get('enquiryAmount',"0")) > 1000 and (today - datetime_object).days > 60:
        enquiry_count += 1

    # build response
    resp = {}
    resp["income_category"] = income_cat
    resp["enquiry"] = enquiry_count
    resp["income"] = predicted_income

    status_code = 200
    response = {
        "statusCode": status_code,
        "data": resp
    }

    return response
