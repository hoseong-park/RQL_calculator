import streamlit as st
import cantera as ct
import numpy as np
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
# 웹 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="RQL Combustor Simulator", layout="wide")

header_col1, header_col2 = st.columns([0.4, 0.6])

with header_col1:
    st.title("RQL Combustor simulator")
    st.write("Adjust the variables and click the [Calculation] button.")
with header_col2:
    st.image("combustor2.png", caption="RQL Combustor Schematic Diagram", width=500)

# 1. 사이드바 - 입력 변수 세팅 구역
st.sidebar.header("Variables")

mech_database = {
    "GRI 3.0": {
        "path": "gri30.yaml",
        "desc": """
        - **C** (species: 53, reactions: 325)
                """
    },
    "CRECK(2023C)": {
        # "path": get_mech_path("Mechanisms/CRECK(2023C)/CRECK(2023C).yaml)",r"D:\4. python code\Cantera\Mechanisms\CRECK(2023C)\CRECK(2023C).yaml"),
        "path": "CRECK(2023C).yaml",
        "desc": """
        - **C1_C3** (species: 159, reactions: 2459)
        - Temperature: **High**
        - **NOx**
        """
    },    
    
    "CRECK(2023-NH3-H2)": {
        # "path": get_mech_path("Mechanisms/CRECK(2023-NH3)/CRECK(2023-NH3-H2.yaml)", r"D:\4. python code\Cantera\Mechanisms\CRECK(2023-NH3)\CRECK(2023-NH3-H2).yaml"),
        "path": "CRECK(2023-NH3-H2).yaml",
        "desc": """
        - **NH3-H2** (species: 34, reactions: 256)
        - Pressure: ****
        - ****
        """
    },

    "Okafor(2018)": {
        # "path": get_mech_path("Mechanisms/Okarfor (2018)/Okarfor(2018).yaml", r"D:\4. python code\Cantera\Mechanisms\Okarfor (2018)\Okarfor(2018).yaml"),
        "path": "Okarfor(2018).yaml",
        "desc": """
        - **NH3-CH4** (species: 59, reactions: 356)
        - Pressure: **Ambient**
        - Equivalence ratio: 0.8~1.2
        """
    },
    "Mei(2021)":{
        # "path": get_mech_path("Mechanisms/Mei (2021)/Mei_mechanism.yaml", r"D:\4. python code\Cantera\Mechanisms\Mei (2021)\Mei_mechanism.yaml"),
        "path": "Mei_mechanism.yaml",
        "desc": """
        - **NH3-H2-N2 (cracking)** (species: 40, reactions: 257)
        - Pressure: **High(~10 bar)**
        - Equivalence ratio: 0.7~1.4
        """
    },

    "Stagni(2023)": {
        # "path": get_mech_path("Mechanisms/Stagni(2023)/Stagni(2023).yaml", r"D:\4. python code\Cantera\Mechanisms\Stagni(2023)\Stagni(2023).yaml"),
        "path": "Stagni(2023).yaml",
        "desc": """
        - **NH3-H2** (species: 29, reactions: 203)
        - Temperature: **High**
        - ****
        """
    },

    "Nakamura(2017)": {
        # "path": get_mech_path("Mechanisms/Nakamura(2017)/Nakamura(2017).yaml", r"D:\4. python code\Cantera\Mechanisms\Nakamura(2017)\Nakamura(2017).yaml"),
        "path": "Nakamura(2017).yaml",
        "desc": """
        - **NH3** (species: 38, reactions: 232)
        - Pressure: **Ambient**
        - Temperature: **low**
        - Equivalence ratio: 0.8~1.2
        """
    },

    "Zhang(2021)": {
        # "path": get_mech_path("Mechanisms/Zhang(2021)/Zhang(2021).yaml", r"D:\4. python code\Cantera\Mechanisms\Zhang(2021)\Zhang(2021).yaml"),
        "path": "Zhang(2021).yaml",
        "desc": """
        - **NH3** (species: 38, reactions: 263)
        - Pressure: **Ambient**
        - Temperature: **low~high**
        - Equivalence ratio: 0.25~1.00
        """
    }

    }

# 1. 드롭다운 선택창
selected_mech_name = st.sidebar.selectbox("Mechanism", list(mech_database.keys()))

# 2. 선택된 메커니즘의 데이터 추출
chosen_mech_path = mech_database[selected_mech_name]["path"]
chosen_mech_desc = mech_database[selected_mech_name]["desc"]

# [핵심] 사이드바에 접이식 설명 상자 배치 (클릭하면 텍스트가 슥 아래로 나옴)
with st.sidebar.expander("Mechanism explanation"):
    st.markdown(chosen_mech_desc)

# 1-1. 온도 및 압력
st.sidebar.subheader("Fuel/air condition")
T_fuel_raw = st.sidebar.text_input("Fuel temperature (℃)", value="15")
T_air_raw = st.sidebar.text_input("Air temperature (℃)", value="453.552785761")
P_raw = st.sidebar.text_input("Combustor pressure (Pa)", value="1983838.2237")

# 1-2.燃料 몰분율
st.sidebar.subheader("Fuel composition (sum = 100)")
mole_CH4 = st.sidebar.slider("CH4", 0, 100, 0)
mole_H2 = st.sidebar.slider("H2", 0, 100, 0)
mole_NH3 = st.sidebar.slider("NH3", 0, 100, 100)

# 1-3. 질량 유량
st.sidebar.subheader("Mass flow rate")
mdot_fuel_raw = st.sidebar.text_input("Primary fuel (kg/s)", value="0.384069365166667")  # 예시 값 직접 입력
mdot_air_raw = st.sidebar.text_input("Primary air (kg/s)", value="1.81484786695")   # 예시 값 직접 입력
mdot_sec_air_raw = st.sidebar.text_input("Secondary air (kg/s)", value="4.23464502288333")

# 1-4. 반응기 형상 및 내부 온도 조건
st.sidebar.subheader("Reactor setting")
psr1_init_T_raw = st.sidebar.text_input("(Temperature) A-B, primary zone ($K$)", value="2000")

auto_vol = st.sidebar.checkbox("Auto primary volume (Find min vol)", value=False)
if auto_vol:
    psr1_vol_raw = st.sidebar.text_input("(Volume) A-B ($m^3$)", value="-", disabled=True)
    psr1_vol_raw_A = st.sidebar.text_input("(auto_initial) Reaction volume ($m^3$)", value="0.001")
else:
    psr1_vol_raw = st.sidebar.text_input("(Volume) A-B ($m^3$)", value="0.001")
    psr1_vol_raw_A = st.sidebar.text_input("(auto_initial) Reaction volume ($m^3$)", value="-", disabled=True)


# auto_vol2 = st.sidebar.checkbox("Auto secondary volume (Find min vol)", value=False)
# if auto_vol2:
#     psr2_vol_raw = st.sidebar.text_input("(s) Reaction volume ($m^3$)", value="-", disabled=True)
#     psr2_vol_raw_A = st.sidebar.text_input("(s-auto_initial) Reaction volume ($m^3$)", value="0.05")
# else:
psr2_vol_raw = st.sidebar.text_input("(Volume) C-D ($m^3$)", value="0.001")
# psr2_vol_raw_A = st.sidebar.text_input("(s-auto_initial) Reaction volume ($m^3$)", value="-", disabled=True)

# psr2_vol_raw = st.sidebar.text_input("(s) Reaction volume ($m^3$)", value="0.05")
pfr1_area_raw = st.sidebar.text_input("(Area) Primary - Combustor cross secion area ($m^2$)", value="0.041547562843725")
pfr2_area_raw = st.sidebar.text_input("(Area) secondary - Combustor cross secion area ($m^2$)", value="0.041547562843725")

pfr1_len_raw = st.sidebar.text_input("(Length) A-C ($m$)", value="0.454")
pfr2_len_raw = st.sidebar.text_input("(Length) C-E ($m$)", value="0.454")

# %% 2. 메인 화면 - 계산 버튼 및 결과 출력 구역
if st.button("Calculation", type="primary"):
    # 사용자가 입력한 문자열을 Cantera가 인식할 수 있게 숫자로 변환
    T_fuel = float(T_fuel_raw) + 273.15  # ℃를 K로 변환
    T_air = float(T_air_raw) + 273.15    # ℃를 K로 변환
    P = float(P_raw)
    
    mdot_fuel = float(mdot_fuel_raw)
    mdot_air = float(mdot_air_raw)
    mdot_sec_air = float(mdot_sec_air_raw)

    psr1_init_T = float(psr1_init_T_raw)
    if auto_vol:
        psr1_vol_initial = float(psr1_vol_raw_A)
    else:
        psr1_vol = float(psr1_vol_raw)

    pfr1_area = float(pfr1_area_raw)
    pfr1_len = float(pfr1_len_raw)
    
    # psr2_vol = float(psr2_vol_raw)
    # if auto_vol2:
    #     psr2_vol_initial = float(psr2_vol_raw_A)
    # else:
    psr2_vol = float(psr2_vol_raw)

    pfr2_area = float(pfr2_area_raw)
    pfr2_len = float(pfr2_len_raw)
    with st.spinner("Running Cantera Solver ..."):
        try:
            
            # Cantera 초기화
            # gas = ct.Solution('gri30.yaml')
            gas = ct.Solution(chosen_mech_path)
            if mole_CH4 == 0:
                fuel_species = f"H2:{mole_H2}, NH3:{mole_NH3}"
            else:
                fuel_species = f"CH4:{mole_CH4}, H2:{mole_H2}, NH3:{mole_NH3}"

            air_species = "O2:0.21, N2:0.79"
            
            Actual_AF = mdot_air / mdot_fuel
            stoich_AF = gas.stoich_air_fuel_ratio(fuel_species, air_species, basis='mole')
            phi1 = stoich_AF / Actual_AF

            Actual_AF2 = (mdot_air + mdot_sec_air) / mdot_fuel
            stoich_AF2 = gas.stoich_air_fuel_ratio(fuel_species, air_species, basis='mole')
            phi2 = stoich_AF2 / Actual_AF2
            # ----------------------------------------------------
            # [단계 1] PSR 1 계산
            # ----------------------------------------------------
            gas.TPX = T_fuel, P, fuel_species
            fuel_inlet = ct.Reservoir(gas, clone=False)
            gas.TPX = T_air, P, air_species
            air_inlet = ct.Reservoir(gas, clone=False)
            outlet_1 = ct.Reservoir(gas, clone=False)

            if auto_vol:
                # 🛠️ 자동 볼륨 탐색 알고리즘
                current_vol = psr1_vol_initial 
                vol_step = 0.0001     
                max_iter = 1000        
                iter_cnt = 0
                
                while iter_cnt < max_iter:
                    gas.TPX = psr1_init_T, P, air_species
                    psr1 = ct.IdealGasReactor(gas, clone=False)
                    psr1.volume = current_vol
                    
                    mfc_f = ct.MassFlowController(fuel_inlet, psr1, mdot=mdot_fuel)
                    mfc_a = ct.MassFlowController(air_inlet, psr1, mdot=mdot_air)
                    valve_1 = ct.Valve(psr1, outlet_1, K=1.0)
                    
                    sim_psr1 = ct.ReactorNet([psr1])
                    sim_psr1.advance_to_steady_state()
                    
                    # 온도가 1000K를 넘으면 루프 탈출
                    if psr1.phase.T >= 1000.0:
                        psr1.volume = current_vol
                        break
                    current_vol += vol_step
                    iter_cnt += 1
                else:
                    raise Exception("PSR1 자동 부피 설정 실패: 최대 반복 횟수 도달")
            else:
                gas.TPX = psr1_init_T, P, air_species
                psr1 = ct.IdealGasReactor(gas, clone=False)
                psr1.volume = psr1_vol
            
                mfc_f = ct.MassFlowController(fuel_inlet, psr1, mdot=mdot_fuel)
                mfc_a = ct.MassFlowController(air_inlet, psr1, mdot=mdot_air)
                valve_1 = ct.Valve(psr1, outlet_1, K=1.0)
                
                sim_psr1 = ct.ReactorNet([psr1])
                sim_psr1.advance_to_steady_state()

            mdot_total_1 = mdot_fuel + mdot_air
            tau_psr1 = (psr1.phase.density * psr1.volume) / mdot_total_1
            length_psr1 = psr1.volume / pfr1_area
            
            x_length = []
            x_temperature = []
            x_NOx = []
            x_NH3 = []
            x_tau = []

            x_length.append(length_psr1)
            x_temperature.append(psr1.phase.T)
            x_tau.append(tau_psr1)
            idx_NO = gas.species_index('NO')
            idx_NO2 = gas.species_index('NO2')
            idx_NH3 = gas.species_index('NH3')
            idx_H2O = gas.species_index('H2O')
            idx_O2 = gas.species_index('O2')

            x_NOx.append((psr1.phase.X[idx_NO]+psr1.phase.X[idx_NO2])*1e6/(1-psr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr1.phase.X[idx_O2])))
            x_NH3.append((psr1.phase.X[idx_NH3])*1e6/(1-psr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr1.phase.X[idx_O2])))

            # ----------------------------------------------------
            # [단계 2] PFR 1 계산 (길이 기준 보폭 루프)
            # ----------------------------------------------------
            gas.TPX = psr1.phase.T, psr1.phase.P, psr1.phase.X
            pfr1 = ct.IdealGasConstPressureReactor(gas, clone=False)
            sim_pfr1 = ct.ReactorNet([pfr1])
            
            x_cur = length_psr1
            t_cum1 = 0.0
            dx = 0.005
            length_count = 1
            KK = 1
            tau_pfr1 = tau_psr1
            if x_cur >= pfr1_len:
                x_cur = 0
                KK = 0

            while x_cur < pfr1_len:
                v = mdot_total_1 / (pfr1.phase.density * pfr1_area)
                t_cum1 += (dx / v)
                sim_pfr1.advance(t_cum1)
                x_cur += dx
                tau_pfr1 += (dx / v)

                x_length.append(x_cur)
                x_temperature.append(pfr1.phase.T)
                x_NOx.append((pfr1.phase.X[idx_NO]+pfr1.phase.X[idx_NO2])*1e6/(1-pfr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr1.phase.X[idx_O2])))
                x_NH3.append((pfr1.phase.X[idx_NH3])*1e6/(1-pfr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr1.phase.X[idx_O2])))
                x_tau.append(tau_pfr1)

                length_count=length_count+1
                
            # ----------------------------------------------------
            # [단계 3] 2차 공기 단열 혼합 및 PSR 2 계산
            # ----------------------------------------------------
            pfr1_out_q = ct.Quantity(gas, constant='HP')
            pfr1_out_q.TPX = pfr1.phase.T, P, pfr1.phase.X
            pfr1_out_q.mass = mdot_total_1
            
            sec_air_q = ct.Quantity(gas, constant='HP')
            sec_air_q.TPX = T_air, P, air_species # 2차 공기도 T_air와 동일하다고 가정
            sec_air_q.mass = mdot_sec_air
            
            mix2 = pfr1_out_q + sec_air_q
            mdot_total_2 = mdot_total_1 + mdot_sec_air
            
            gas.TPX = mix2.T, mix2.P, mix2.X
            psr2_inlet = ct.Reservoir(gas, clone=False)
            outlet_2 = ct.Reservoir(gas, clone=False)
            
            # if auto_vol2:
            #     # 🛠️ 자동 볼륨 탐색 알고리즘
            #     current_vol2 = psr2_vol_initial 
            #     vol_step = 0.0001     
            #     max_iter = 1000        
            #     iter_cnt = 0
                
            #     while iter_cnt < max_iter:
            #         gas.TPX = psr1_init_T, P, air_species
            #         psr2 = ct.IdealGasReactor(gas, clone=False)
            #         psr2.volume = current_vol2
                    
            #         mfc_f = ct.MassFlowController(fuel_inlet, psr2, mdot=mdot_fuel)
            #         mfc_a = ct.MassFlowController(air_inlet, psr2, mdot=mdot_air)
            #         valve_2 = ct.Valve(psr2, outlet_2, K=1.0)
                    
            #         sim_psr2 = ct.ReactorNet([psr2])
            #         sim_psr2.advance_to_steady_state()
                    
            #         # 온도가 1000K를 넘으면 루프 탈출
            #         if psr2.phase.T >= 1000.0:
            #             psr2.volume = current_vol2
            #             break
                    
            #         current_vol2 += vol_step
            #         iter_cnt += 1
            #     else:
            #         raise Exception("PSR1 자동 부피 설정 실패: 최대 반복 횟수 도달")
            # else:
            psr2 = ct.IdealGasReactor(gas, clone=False)
            psr2.volume = psr2_vol
            mfc_psr2 = ct.MassFlowController(psr2_inlet, psr2, mdot=mdot_total_2)
            valve_2 = ct.Valve(psr2, outlet_2, K=1.0)
            
            sim_psr2 = ct.ReactorNet([psr2])
            sim_psr2.advance_to_steady_state()
            
            tau_psr2 = (psr2.phase.density * psr2.volume) / mdot_total_2
            length_psr2 = psr2.volume / pfr2_area
            length_psr22 = length_psr2

            x_length.append(x_cur + length_psr22)
            x_temperature.append(psr2.phase.T)
            x_NOx.append((psr2.phase.X[idx_NO]+psr2.phase.X[idx_NO2])*1e6/(1-psr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr2.phase.X[idx_O2])))
            x_NH3.append((psr2.phase.X[idx_NH3])*1e6/(1-psr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr2.phase.X[idx_O2])))
            x_tau.append(tau_pfr1+tau_psr2)

            length_count = length_count + 1

            # ----------------------------------------------------
            # [단계 4] PFR 2 계산
            # ----------------------------------------------------
            gas.TPX = psr2.phase.T, psr2.phase.P, psr2.phase.X
            pfr2 = ct.IdealGasConstPressureReactor(gas, clone=False)
            sim_pfr2 = ct.ReactorNet([pfr2])
            
            x_cur2 = x_cur+length_psr2
            t_cum2 = 0.0
            tau_pfr2 = tau_pfr1+tau_psr2
            if length_psr2 >= pfr2_len:
                x_cur2 = 0
                KK = 0
            while length_psr2 < pfr2_len:
                v2 = mdot_total_2 / (pfr2.phase.density * pfr2_area)
                t_cum2 += (dx / v2)
                tau_pfr2 += (dx/v2)
                sim_pfr2.advance(t_cum2)
                x_cur2 += dx
                length_psr2 += dx

                x_length.append(x_cur2)
                x_temperature.append(pfr2.phase.T)
                x_NOx.append((pfr2.phase.X[idx_NO]+pfr2.phase.X[idx_NO2])*1e6/(1-pfr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr2.phase.X[idx_O2])))
                x_NH3.append((pfr2.phase.X[idx_NH3])*1e6/(1-pfr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr2.phase.X[idx_O2])))
                x_tau.append(tau_pfr2)

                # length_count=length_count+1
            
            # ----------------------------------------------------
            # 📊 결과 리포트 출력 구역
            # ----------------------------------------------------
            if psr1.phase.T < 1000:
                st.error(f"No reaction in primary zone. Please enter higher temperature or volume.")
            elif KK == 0:
                st.error(f"Please control combustor length.")
            else:
                st.success("Calculation compeleted")

            
            # 메트릭 카드로 중요 수치 대시보드화
            idx_NO = gas.species_index('NO')
            idx_NO2 = gas.species_index('NO2')
            idx_NH3 = gas.species_index('NH3')
            
            col1, col7, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("Exit temperature", f"{pfr2.phase.T:.1f} K")
            col7.metric("Exit temperature", f"{pfr2.phase.T-273.15:.1f} C")
            col2.metric("Primary $\phi$", f"{phi1:.4f}")
            col3.metric("Total $\phi$", f"{phi2:.4f}")
            col4.metric("Residence time", f"{(tau_psr1+tau_psr2+t_cum1+t_cum2)*1e3:.2f} ms")
            col5.metric("Exit NOx (NO+NO2)", f"{(pfr2.phase.X[idx_NO]+pfr2.phase.X[idx_NO2])*1e6/(1-pfr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr2.phase.X[idx_O2])):.2f} ppmvd@15%O2")
            col6.metric("Exit NH3 Slip", f"{pfr2.phase.X[idx_NH3]*1e6/(1-pfr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr2.phase.X[idx_O2])):.2f} ppmvd@15%O2")
            
            # 표 형태로 상세 데이터 나열
            st.subheader("Data")
            data = {
                "Session": ["Primary reaction(A-B)", "Post flame zone1(B-C)", "Secondary reaction(C-D)", "Emissions probe(E)"],
                "Temperature (K)": [f"{psr1.phase.T:.1f}", f"{pfr1.phase.T:.1f}", f"{psr2.phase.T:.1f}", f"{pfr2.phase.T:.1f}"],
                "length (mm)": [f"(A-B) {length_psr1*1e3:.4f}", f"(A-C) {x_cur*1e3:.4f}", f"(A-D) {(x_cur+length_psr22)*1e3:.4f}", f"(A-E) {x_cur2*1e3:.4f}"],
                "Residence time (ms)": [f"{tau_psr1*1e3:.2f}", f"{t_cum1*1e3:.2f}", f"{tau_psr2*1e3:.2f}", f"{t_cum2*1e3:.2f}"],
                "Volume (m^3)": [f"{psr1.volume:.4f}", "-", f"{psr2.volume:.4f}", "-"],                
                "NOx (ppmvd@15%O2)": [f"{(psr1.phase.X[idx_NO]+psr1.phase.X[idx_NO2])*1e6/(1-psr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr1.phase.X[idx_O2])):.1f}",
                              f"{(pfr1.phase.X[idx_NO]+pfr1.phase.X[idx_NO2])*1e6/(1-pfr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr1.phase.X[idx_O2])):.1f}", 
                              f"{(psr2.phase.X[idx_NO]+psr2.phase.X[idx_NO2])*1e6/(1-psr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr2.phase.X[idx_O2])):.1f}", 
                              f"{(pfr2.phase.X[idx_NO]+pfr1.phase.X[idx_NO2])*1e6/(1-pfr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr2.phase.X[idx_O2])):.1f}"],
                "NH3 (ppmvd@15%O2)": [f"{psr1.phase.X[idx_NH3]*1e6/(1-psr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr1.phase.X[idx_O2])):.1f}", 
                              f"{pfr1.phase.X[idx_NH3]*1e6/(1-pfr1.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr1.phase.X[idx_O2])):.1f}", 
                              f"{psr2.phase.X[idx_NH3]*1e6/(1-psr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-psr2.phase.X[idx_O2])):.1f}", 
                              f"{pfr2.phase.X[idx_NH3]*1e6/(1-pfr2.phase.X[idx_H2O]*(0.21 - 0.15)/(0.21-pfr2.phase.X[idx_O2])):.1f}"],
            }

            
            # st.dataframe(data, use_container_width=True)
            st.dataframe(data, width='stretch')
            # st.image(r"D:\4. python code\Cantera\combustor.png", caption="RQL Combustor Schematic Diagram", width=700)

            
            if KK == 1:
                # 1. 데이터를 확실하게 실수형(float) 리스트로 변환
                plot_x = [float(x)*1000 for x in x_length]
                T_plot_y = [float(y) for y in x_temperature]
                NOx_plot_y = [float(y) for y in x_NOx]
                NH3_plot_y = [float(y) for y in x_NH3]
                tau_plot_y = [float(y)*1000 for y in x_tau]

                linewidth = 1
                fontsize_label = 8
                fontsize_legend = 5
                fontsize_tick = 5
                grid_alpha = 0.6
            

                # 3. 그래프 피겨(Figure) 생성 및 그리기
                fig, ax = plt.subplots(nrows = 1, ncols = 3, figsize=(800 / 100, 250 / 100,), dpi = 100)

                ax[0].plot(plot_x, T_plot_y, color="royalblue", linewidth=linewidth, linestyle="-", label="Temperature (K)")                
                ax[0].axvline(x=(x_cur+length_psr22)*1e3, color="firebrick", linestyle=":", linewidth=0.8, alpha=0.8)
                # ax.set_title("Axial Temperature Profile along Combustor", fontsize=14, fontweight="bold", pad=15)
                ax[0].set_xlabel("Combustor Length (mm)", fontsize=fontsize_label)
                ax[0].set_ylabel("Temperature (K)", fontsize=fontsize_label)
                ax[0].tick_params(axis='both', labelsize=fontsize_tick)
                ax[0].grid(True, linestyle=":", alpha=grid_alpha)
                ax[0].legend(loc="upper right", fontsize=fontsize_legend)
                

                ax[1].plot(plot_x, NOx_plot_y, color="k", linewidth=linewidth, linestyle="-", label="NOx")                
                ax[1].axvline(x=(x_cur+length_psr22)*1e3, color="firebrick", linestyle=":", linewidth=0.8, alpha=0.8)
                # ax.set_title("Axial Temperature Profile along Combustor", fontsize=14, fontweight="bold", pad=15)
                ax[1].set_xlabel("Combustor Length (mm)", fontsize=fontsize_label)
                # ax[1].set_ylabel("NOx (ppmvd)", fontsize=fontsize_label)
                ax[1].tick_params(axis='both', labelsize=fontsize_tick)
                ax[1].grid(True, linestyle=":", alpha=grid_alpha)
                ax[1].legend(loc="upper right", fontsize=fontsize_legend)

                ax[2].plot(plot_x, NH3_plot_y, color="c", linewidth=linewidth, linestyle="-", label="NH3")                
                ax[2].axvline(x=(x_cur+length_psr22)*1e3, color="firebrick", linestyle=":", linewidth=0.8, alpha=0.8)
                # ax.set_title("Axial Temperature Profile along Combustor", fontsize=14, fontweight="bold", pad=15)
                ax[2].set_xlabel("Combustor Length (mm)", fontsize=fontsize_label)
                # ax[2].set_ylabel("NH3 (ppmvd)", fontsize=fontsize_label)
                ax[2].tick_params(axis='both', labelsize=fontsize_tick)
                ax[2].grid(True, linestyle=":", alpha=grid_alpha)
                ax[2].legend(loc="upper right", fontsize=fontsize_legend)

                # 4. Streamlit 전용 출력 함수 사용하여 웹에 띄우기
                st.pyplot(fig, use_container_width=False)
                
                with st.expander("Temperature data", expanded=False):
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,  # 변환된 데이터 전달
                            y=T_plot_y,  # 변환된 데이터 전달
                            name="Temperature (K)",
                            line=dict(color="royalblue", width=3, dash="dash")
                        )
                    )
                    fig.update_layout(
                        title_text="<b>Axial Temperature Profile along Combustor</b>",
                        hovermode="x unified",
                        xaxis_title="<b>Combustor Length (m)</b>",
                        yaxis_title="<b>Temperature (K)</b>"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with st.expander("NOx data", expanded=False):
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,  # 변환된 데이터 전달
                            y=NOx_plot_y,  # 변환된 데이터 전달
                            name="NOx (ppmvd@15%O2)",
                            line=dict(color="royalblue", width=3, dash="dash")
                        )
                    )
                    fig.update_layout(
                        title_text="<b>Axial NOx Profile along Combustor</b>",
                        hovermode="x unified",
                        xaxis_title="<b>Combustor Length (m)</b>",
                        yaxis_title="<b>NOx (ppmvd@15%O2)</b>"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with st.expander("NH3 data", expanded=False):
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,  # 변환된 데이터 전달
                            y=NH3_plot_y,  # 변환된 데이터 전달
                            name="NH3 (ppmvd@15%O2)",
                            line=dict(color="royalblue", width=3, dash="dash")
                        )
                    )
                    fig.update_layout(
                        title_text="<b>Axial NH3 Profile along Combustor</b>",
                        hovermode="x unified",
                        xaxis_title="<b>Combustor Length (m)</b>",
                        yaxis_title="<b>NH3 (ppmvd@15%O2)</b>"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with st.expander("Residence time", expanded=False):
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,  # 변환된 데이터 전달
                            y=tau_plot_y,  # 변환된 데이터 전달
                            name="Residence time (ms)",
                            line=dict(color="royalblue", width=3, dash="dash")
                        )
                    )
                    fig.update_layout(
                        title_text="<b>Axial residence time Profile along Combustor</b>",
                        hovermode="x unified",
                        xaxis_title="<b>Combustor Length (m)</b>",
                        yaxis_title="<b>Residence time (ms) </b>"
                    )
                    st.plotly_chart(fig, use_container_width=True)


            

            # if KK == 1:
            #     # 🌟 데이터 타입을 강제로 float로 변환하여 안전성 확보
            #     plot_x = [float(x) for x in x_length]
            #     plot_y = [float(y) for y in x_temperature]

            #     fig = go.Figure()
            #     fig.add_trace(
            #         go.Scatter(
            #             x=plot_x,  # 변환된 데이터 전달
            #             y=plot_y,  # 변환된 데이터 전달
            #             name="Temperature (K)",
            #             line=dict(color="royalblue", width=3, dash="dash")
            #         )
            #     )
            #     fig.update_layout(
            #         title_text="<b>Axial Temperature Profile along Combustor</b>",
            #         hovermode="x unified",
            #         xaxis_title="<b>Combustor Length (m)</b>",
            #         yaxis_title="<b>Temperature (K)</b>"
            #     )
                
            #     st.plotly_chart(fig, use_container_width=True)


        except Exception as e:
            st.error(f"계산 중 에러가 발생했습니다. 입력 조건을 확인하세요.\n에러 내용: {e}")
