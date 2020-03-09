import requests
import re
import json
import pickle as pkl
import pandas as pd
from bs4 import BeautifulSoup as bs4


class Data:
    
    def __init__(self, reg_num):
        self.reg_num = reg_num
        self.base_url = 'https://w2.brreg.no/motorvogn/'
        self.soup = self.get_soup()
        self.moresoup = self.get_more_soup()
        self.dagboknr = self.dagboknr_liste("nr")
        self.dagbokdate = self.dagboknr_liste("date")
        self.invidpant = self.get_invid_pant("list")
        self.invidpantsummed = self.get_invid_pant("summed")
        self.innsenderliste = self.innsender_list()
        self.innsendergate = self.innsender_gate()
        self.nonumbersInn = self.no_numbers_list()
        self.InnNumberList = self.numbers_list()
        self.utpanthaverList = self.utpanthaver_list()
        self.utpanthaverGate = self.utpanthaver_gate()
        self.emailsdict = self.reload_pickle()
    
    def __repr__(self):
        return f"Data('{self.reg_num}')"       
        
    def __str__(self):
        data = self.dict_maker()
        representation=f"{'Kjøretøy:':<20}{self.reg_num}\n\n"
        for i in data:
            representation+=f"{'Utpanthaver: ':<20}{data[i]['Utpanthaver']:30}{data[i]['KR']:>15}\n"
        representation+=f"{'Sum:':<56}{sum(self.invidpant):.2f}"
        return representation
    
    def reload_pickle(self):
        """
        This opens a dict of emails that has all the debt collectors i know the email adress to. 
        To start your own dict you should add this code:

        ***********
        
        a = {"Debt-collecter-brreg-number" : "email@email"}

        with open('emails.pkl', 'wb') as handle:
            pkl.dump(a, handle, protocol=pkl.HIGHEST_PROTOCOL)

        ***********

        You can nest your dict for multiple emailadresses according to what team at the debt collector you want to send the email to, will add better support for this in get_emails()
        """
        with open('emails.pkl', 'rb') as handle:
            b = pkl.load(handle)

        return b
    
    def get_emails(self, nested):
        """
        This produces a list of emails that is connected to the Debt collectors.
        "nested" is an identifier for nested dicts.
        TODO: Better nested support.
        """
        emailslist = []
        for k, v in self.emailsdict.items():
            if k in nested:
                for ki, vi in v.items():
                    if ki in self.InnNumberList:
                        emailslist.append(vi)
            elif k in self.InnNumberList:
                emailslist.append(v)
        
        return emailslist


    def get_soup(self):
        brregurl = (f"{self.base_url}/heftelser_motorvogn.jsp?regnr={self.reg_num}")
        s = requests.session()
        r = s.get(brregurl)
        soup = bs4(r.content, 'lxml')
        return soup
        
    def get_invid_pant(self, listorsummed):
        NOKList = []
        NOKListSummed = []
        for td in self.soup.findAll("td", align="right")[1:]:
            NOK = float(td.get_text().replace(",",".").replace(" ",""))
            NOKList.append(NOK)
            NOKListSummed.append(sum(NOKList))
        if listorsummed == "list":
            return NOKList
        elif listorsummed == "summed":
            return NOKListSummed
        else:
            print("The List or Summed argument is not valid")
            
    def get_more_soup(self):
        pre = []
        for td in self.soup.findAll("td", align="left"):
            for a in td.findAll("a", href=True):
                moresoup = bs4(requests.get(f"{self.base_url}{a['href']}").text, 'lxml')
                pre.append(moresoup.find("pre"))
        return pre        
    
    def dagboknr_liste(self, nrdateordict):
        """
        "date" gives you the list of "Dagboknr"-dates, "nr" gives you the "Dagboknr"-number. I'm guessing no one would ever need just the list of dates by them selves, so i've added the option to get them also as a dict.
        """
        DagbokNrDatoDict = {}
        DagboknrListe = []
        DagbokDatoListe = []
        pre = self.moresoup
        for i in pre:
            string = re.findall("(?<=Dagbokdato<br/> ).*(?=<br/>)", str(i))[0]
            Dagboknr = re.findall("(?<=).*(?= )", str(string))[0]
            DagbokDato = re.findall("(?<= ).*(?=$)", str(string))[0]
            DagboknrListe.append(Dagboknr)
            DagbokDatoListe.append(DagbokDato)
            DagbokNrDatoDict[Dagboknr] = DagbokDato
            
        if nrdateordict == "nr":
            return DagboknrListe
        elif nrdateordict == "date":
            return DagbokDatoListe
        elif nrdateordict == "dict":
            return DagbokNrDatoDict    
        else:
            print("The List or Summed argument is not valid")
    
    def innsender_list(self):
        InnsenderList = []
        pre = self.moresoup
        for i in pre:
            Innsender = re.search("Innsender (.+?)     ", i.text).group(1)
            InnsenderList.append(Innsender)
            
        return InnsenderList
    
    def innsender_gate(self):
        InnsenderGateList = []
        pre = self.moresoup
        i_regex = r"(?<=Innsender).*(?=<br\/> )"
        i_gate_regex = r"(?<=                            ).*(?=<br\/>                            )"
        i_adr_regex = r"(?<=             )[0-9].*(?=$)"
        for i in pre:
            RegexString = re.findall(i_regex, str(i))[0]
            utpantHaverGate = re.findall(i_gate_regex, str(RegexString))[0].strip()
            utpantHaverPostnr = re.findall(i_adr_regex, str(RegexString))[0]
            appendstring = f"{utpantHaverGate}, {utpantHaverPostnr}"
            InnsenderGateList.append(appendstring)
            
        return InnsenderGateList
    
    def no_numbers_list(self):
        InnsenderList = self.innsenderliste
        nonumbersInnList = []
        for i in InnsenderList:
            nonumbersInn = re.sub('[0-9]','', i).strip()
            nonumbersInnList.append(nonumbersInn)
        return nonumbersInnList
    
    def numbers_list(self):
        InnsenderList = self.innsenderliste
        InnNumberList = []
        for i in InnsenderList:
            InnNumber = re.sub('[^0-9]','', i)
            InnNumberList.append(InnNumber)
        return InnNumberList
    
    def utpanthaver_list(self):
        UtPantHaverList = []
        pre = self.moresoup
        UtHaverRegex = r"(?<=Utlegg til fordel for<br\/>).*(?=Org.nr)"
        SpantRegex = r"(?<=Salgspant i motorvogner:).*(?=<br\/>)"
        UtenlandsRegex = r"(?<=Utlegg til fordel for<br\/>).*?(?=<br/>)"
        for i in pre:
            if "Org.nr" in str(i):
                if re.findall(UtHaverRegex, str(i)):
                    utpantHaver = re.findall(UtHaverRegex, str(i))[0].strip()
                    UtPantHaverList.append(utpantHaver)
                elif re.findall(SpantRegex, str(i)):
                    utpantHaver = r"SALGSPANT"
                    UtPantHaverList.append(utpantHaver)
            else:
                utpantHaver = re.findall(UtenlandsRegex, str(i))[0].strip()
                UtPantHaverList.append(utpantHaver)

        return UtPantHaverList
    
    def utpanthaver_org(self):
        UtPantHaverOrgList = []
        pre = self.moresoup
        UtHaverOrgRegex = r"(?<=Org.nr )[0-9 ]*[0-9]*[0-9]"
        for i in pre:
            if re.findall(UtHaverOrgRegex, str(i)):
                utpantHaverOrg = re.findall(UtHaverOrgRegex, str(i))[0]
                UtPantHaverOrgList.append(utpantHaverOrg) 
        return UtPantHaverOrgList
        
    def utpanthaver_gate(self):
        UtPantHaverGateList = []
        pre = self.moresoup
        UtHaverGateRegex = r"(?<=Org.nr).*(?=<br\/> )"
        Gate = r"(?<=             ).*(?=<br\/>             )"
        Postnr = r"(?<=             )[0-9].*(?=$)"
        """
        Postnr regex will work as long as the street name doeasn't start with a number, which it never should.
        TODO: Found pant with foreign address, gave trouble because of the regex change. 
              Added else statement to fix the issue temporarily. 
        """
        for i in pre:
            if re.findall(UtHaverGateRegex, str(i)):
                RegexString = re.findall(UtHaverGateRegex, str(i))[0]
                utpantHaverGate = re.findall(Gate, str(RegexString))[0]
                utpantHaverPostnr = re.findall(Postnr, str(RegexString))[0]
                appendstring = f"{utpantHaverGate}, {utpantHaverPostnr}"
                UtPantHaverGateList.append(appendstring)
            else:
                UtPantHaverGateList.append("Foreign address")
        return UtPantHaverGateList    
    
    def dict_maker(self):
        dictInnUt = {}
        dnr = self.dagboknr
        ddate = self.dagbokdate
        NOK = self.invidpant
        TOTNOK = self.invidpantsummed
        InnsenderList = self.innsenderliste
        InnsenderGate = self.innsendergate        
        nonumbersInnList = self.nonumbersInn       
        UtPantHaverList = self.utpanthaverList
        UtPantHaverGate = self.utpanthaverGate
        InnNumberList = self.InnNumberList
        if len(self.innsenderliste) == 0:
            raise IndexError("There doesn't seem to be any utleggspant")
        for i, y in enumerate(InnsenderList):
            dictInnUt[i] = {} 
            dictInnUt[i]["Dagboknr"] = dnr[i]    
            dictInnUt[i]["Dagboknr Dato"] = ddate[i]
            dictInnUt[i]["Innsendernr"] = InnNumberList[i]
            dictInnUt[i]["Innsender"] = nonumbersInnList[i]
            dictInnUt[i]["Innsender Adr."] = InnsenderGate[i]
            dictInnUt[i]["Utpanthaver"] = UtPantHaverList[i]
            dictInnUt[i]["Utpanthaver Adr."] = UtPantHaverGate[i]
            dictInnUt[i]["KR"] = NOK[i]
            dictInnUt[i]["Tot KR"] = TOTNOK[i] - NOK[i]
            if i == 0:
                dictInnUt[i]["Tot KR kun UT.Pant"] = 0
            else:
                dictInnUt[i]["Tot KR kun UT.Pant"] = f"{(TOTNOK[i] - NOK[i]) - NOK[0]:.2f}"
        
        c = len(InnsenderList)
        
        if dictInnUt[0]["Utpanthaver"] == "SALGSPANT":
            dictInnUt[c] = {}
            dictInnUt[c]["Dagboknr"] = ""           
            dictInnUt[c]["Dagboknr Dato"] = ""
            dictInnUt[c]["Innsendernr"] = ""
            dictInnUt[c]["Innsender"] = ""
            dictInnUt[c]["Innsender Adr."] = ""
            dictInnUt[c]["Utpanthaver"] = ""
            dictInnUt[c]["Utpanthaver Adr."] = ""
            dictInnUt[c]["KR"] = ""
            dictInnUt[c]["Tot KR"] = TOTNOK[len(self.innsenderliste) - 1]
            dictInnUt[c]["Tot KR kun UT.Pant"] = f"{TOTNOK[len(self.innsenderliste) - 1] - NOK[1]:.2f}"

        return dictInnUt
        
    
    def create_dataframe(self, simpleorextended):
        """
        simple does not include the columns "Innsender Adr.", nor "Utpanthaver Adr."
        """
        d = self.dict_maker()
        df = pd.DataFrame.from_dict(d, orient='index')
        if simpleorextended == "simple":
            newdf = df.drop(df.columns[[4, 6]], axis=1)
            return newdf
            with open(f"regnr/{self.reg_num}", "w") as file:
                file.write(json.dumps(newdf))
        else:
            return df
            with open(f"regnr/{self.reg_num}", "w") as file:
                file.write(json.dumps(df))

        


def main():
    pass
    """
    Examples:
    car1 = Data("YOU NEED A REGNR WITH UTLEGGSPANT HERE")
    df = car1.create_dataframe("simple")
    print(car1.dagboknr_liste("dict"))
    print(df.to_string())
    print(car1.get_invid_pant("list"))
    """

if __name__ == "__main__":
    main()
    