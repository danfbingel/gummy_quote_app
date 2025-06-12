import streamlit as st
from fpdf import FPDF
import base64
import pandas as pd
import uuid

st.set_page_config(page_title="Gummy Quote App", layout="centered")

# Initialize storage
if "quotes" not in st.session_state:
    st.session_state.quotes = []

st.title("🍬 Gummy Quote Generator")

# Input Form
with st.form("quote_form"):
    standard = st.checkbox("Standard recipe?", value=True)
    gummy_weight = st.number_input("Gummy weight (g)", 1.5, 5.6, 2.0)
    volume = st.number_input("Number of gummies", 1_000_000, step=1_000)

    actives = []
    for i in range(st.number_input("Number of actives", 0, 10, 0)):
        name = st.text_input(f"Name #{i+1}")
        mg = st.number_input(f"Dosage mg/gummy for {name}", step=0.1)
        cost = st.number_input(f"Cost per kg ($) for {name}", step=0.01)
        actives.append({"name":name,"mg":mg,"cost":cost})
    margin_pct = st.number_input("Margin %", 0.0, 100.0, 10.0)
    shipping_per_kg = st.number_input("Shipping cost per kg ($)", 0.0, 1.0, 0.10)

    submitted = st.form_submit_button("Generate Quote")

def calc_quote():
    def base_price(v):
        if v>=5e6: return 6.00
        if v>=3e6: return 6.50
        return 7.00
    bp = base_price(volume)
    gw_kg = gummy_weight/1000
    act_cost_kg = sum((a["mg"]/1e6)*a["cost"]*1.2 / gw_kg for a in actives)
    raw_kg = bp + act_cost_kg + shipping_per_kg
    final_kg = raw_kg*(1 + margin_pct / 100)
    per_gummy = final_kg * gw_kg
    return {"id":str(uuid.uuid4()),
            "bp":bp,"act":act_cost_kg,"ship":shipping_per_kg,
            "raw":raw_kg,"final":final_kg,"per_gummy":per_gummy}

if submitted:
    q = calc_quote()
    st.session_state.quotes.append(q)

    st.markdown("### 💰 Quote Results")
    st.write(f"**Base $/kg:** ${q['bp']:.2f}")
    st.write(f"**Actives $/kg:** ${q['act']:.2f}")
    st.write(f"**Shipping $/kg:** ${q['ship']:.2f}")
    st.write(f"**Final $/kg:** ${q['final']:.2f}")
    st.write(f"**Cost per gummy:** ${q['per_gummy']:.4f}")

    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(0,10,txt=f"Gummy Quote", ln=1)
    for k,v in q.items():
        if isinstance(v, float):
            pdf.cell(0,8,txt=f"{k}: ${v:.4f}", ln=1)
    pdf_hex = pdf.output(dest="S").encode("latin-1")
    st.download_button("Download Quote PDF", data=pdf_hex,
                       file_name="quote.pdf", mime="application/pdf")

# Admin Panel
st.sidebar.header("Admin Panel")
if st.sidebar.button("Show past quotes"):
    df = pd.DataFrame(st.session_state.quotes)
    st.sidebar.write(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("Download all quotes (CSV)",csv,
                               "quotes.csv","text/csv")