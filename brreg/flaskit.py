from flask import Flask, request, render_template
from brreg import Data

app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template('my-form.html')

@app.route('/', methods=['GET','POST'])
def my_form_post():
    panteliste = []
    if request.method == "POST":
        text = request.form['text']
        processed_text = text.upper()
        brreg = Data(processed_text)
        df = brreg.create_dataframe("simple")
        dagbokdatoer = brreg.dagboknr_liste("date")
        dagboknr = brreg.dagboknr_liste("nr")
        utpanthavere = brreg.utpanthaver_list()
        innsendere = brreg.no_numbers_list()
        Kroner = brreg.get_invid_pant("list")
        emailslist = brreg.get_emails(["5068"])
        emailstring = ";".join(emailslist)

        for i, y in enumerate(dagboknr):
            if utpanthavere[i] == "SALGSPANT":
                continue
            panteliste.append(f" - {dagboknr[i]} {dagbokdatoer[i]} {innsendere[i]} {utpanthavere[i]} Kr. {Kroner[i]};-")

        return render_template('simple.html', tables=[df.to_html(classes='data', header="true")], emailslist= emailstring, panteliste=panteliste, regnr=processed_text)
    
    if IndexError:
        return "There doesn't seem to be any utleggspant"

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0')