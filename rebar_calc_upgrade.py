# -*- coding: utf-8 -*-
import streamlit as st
import math
import pandas as pd
import io

# ============================
# نمایش لوگو و خوش آمدگویی
# ============================
st.set_page_config(layout="wide", page_title="دفتر فنی آرتان")
st.image("icon.png", width=220)
st.title("✍️ خوش آمدید به دفتر فنی آرتان")
st.markdown("**محاسبه‌گر آنلاین میلگرد و بتن با گزارش پرتی و هزینه**")

# ============================
# محاسبه‌گر میلگرد و بتن با گزارش پرتی و هزینه
# ============================

col1, col2, col3 = st.columns(3)
with col1:
    total_concrete_volume = st.number_input("حجم بتن (متر مکعب)", min_value=0.0, value=50.0)
with col2:
    price_rebar = st.number_input("قیمت میلگرد (تومان/کیلوگرم)", min_value=0, value=48000)
with col3:
    price_concrete = st.number_input("قیمت بتن (تومان/متر مکعب)", min_value=0, value=2500000)

st.subheader("ورود لیست میلگردها (قطر میلیمتر و طول قطعه بر متر)")
rebar_df = st.data_editor(
    pd.DataFrame({"قطر (mm)": [16, 14], "طول قطعه (m)": [7.5, 5.2], "تعداد": [20, 15]}),
    use_container_width=True,
    num_rows="dynamic"
)

def get_rebar_weight_per_meter(diameter_mm):
    return (diameter_mm ** 2) / 162.0

def calculate_cutting_and_waste_ffd(pieces_needed, bar_length=12.0):
    if not pieces_needed:
        return 0, []
    pieces = sorted(pieces_needed, reverse=True)
    bars = []
    for piece in pieces:
        placed = False
        for i in range(len(bars)):
            if bars[i] + piece <= bar_length:
                bars[i] += piece
                placed = True
                break
        if not placed:
            bars.append(piece)
    waste_pieces = [bar_length - used for used in bars]
    return len(bars), waste_pieces

if st.button("محاسبه و نمایش نتایج"):
    rebar_data = {}
    for idx, row in rebar_df.iterrows():
        dia = int(row["قطر (mm)"])
        length = float(row["طول قطعه (m)"])
        count = int(row["تعداد"])
        if dia not in rebar_data:
            rebar_data[dia] = []
        rebar_data[dia].extend([length] * count)

    report_data = []
    total_rebar_weight = 0
    total_rebar_cost = 0
    all_waste_data = {}

    for dia, pieces in sorted(rebar_data.items()):
        total_length = sum(pieces)
        weight = total_length * get_rebar_weight_per_meter(dia)
        cost = weight * price_rebar
        total_rebar_weight += weight
        total_rebar_cost += cost
        num_bars_12m, waste_list = calculate_cutting_and_waste_ffd(pieces)
        all_waste_data[dia] = waste_list
        report_data.append({
            "قطر (mm)": dia,
            "طول کل (m)": round(total_length, 2),
            "وزن کل (kg)": round(weight, 2),
            "هزینه (تومان)": int(cost),
            "تعداد شاخه ۱۲ متری": num_bars_12m
        })

    concrete_cost = total_concrete_volume * price_concrete
    total_cost = total_rebar_cost + concrete_cost

    st.subheader("📊 خلاصه نتایج")
    result_df = pd.DataFrame(report_data)
    st.dataframe(result_df, use_container_width=True)

    st.info(f"**وزن کل میلگردها: {total_rebar_weight:.2f} کیلوگرم**")
    st.info(f"**هزینه کل میلگرد: {int(total_rebar_cost):,} تومان**")
    st.info(f"**هزینه بتن: {int(concrete_cost):,} تومان**")
    st.success(f"💰 **هزینه کل مصالح: {int(total_cost):,} تومان**")

    with st.expander("📋 مشاهده پرتی‌ها"):
        for dia, wastes in all_waste_data.items():
            st.write(f"**پرتی میلگرد {dia} میلیمتر:** {', '.join([str(round(w,2)) for w in wastes])} متر")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        result_df.to_excel(writer, index=False, sheet_name='Rebar_Report')
        waste_data = []
        for dia, wastes in all_waste_data.items():
            for w in wastes:
                waste_data.append({"قطر (mm)": dia, "پرتی (m)": w})
        waste_df = pd.DataFrame(waste_data)
        waste_df.to_excel(writer, index=False, sheet_name='Wastes')
        summary_df = pd.DataFrame({"شرح": ["وزن کل میلگرد", "هزینه میلگرد", "هزینه بتن", "هزینه کل"],
                                   "مقدار": [total_rebar_weight, total_rebar_cost, concrete_cost, total_cost]})
        summary_df.to_excel(writer, index=False, sheet_name='Summary')
        writer.save()
        st.download_button(
            label="📥 دانلود گزارش Excel",
            data=buffer,
            file_name="Artan_Rebar_Concrete_Report.xlsx",
            mime="application/vnd.ms-excel"
        )
