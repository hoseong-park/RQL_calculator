import streamlit as st
import cantera as ct
import numpy as np
import os
import sys
#streamlit run RQL_calculator.py
#%%
# def get_mech_path(relative_path, local_absolute_path):
#     """
#     .exe 배포 환경과 내 로컬 PC 개발 환경 모두에서 안전하게 경로를 찾아주는 함수
#     """
#     # PyInstaller가 압축을 푸는 임시 폴더 경로(_MEIPASS)가 존재하는지 확인
#     if hasattr(sys, '_MEIPASS'):
#         # .exe 실행 중이라면 내부 가상 폴더 경로를 반환
#         return os.path.join(sys._MEIPASS, relative_path)
    
#     # 내 컴퓨터에서 그냥 일반 파이썬으로 실행 중이라면 원래 쓰던 절대 경로 반환
#     return local_absolute_path

#%%
# 웹 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="RQL Combustor Simulator", layout="wide")
# 🔥 🛠️ 🌡️ 🧪 ⚖️ 📐 🚀 📋 
st.title("RQL Combustor simulator")
st.write("변수를 조정하고 하단의 **[Calculation]** 버튼을 누르세요.")

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
T_air_raw = st.sidebar.text_input("Air temperature (℃)", value="397")
P_raw = st.sidebar.text_input("Combustor pressure (Pa)", value="1805850")

# 1-2.燃料 몰분율
st.sidebar.subheader("Fuel composition (sum = 100)")
mole_CH4 = st.sidebar.slider("CH4", 0, 100, 0)
mole_H2 = st.sidebar.slider("H2", 0, 100, 0)
mole_NH3 = st.sidebar.slider("NH3", 0, 100, 100)

# 1-3. 질량 유량
st.sidebar.subheader("Mass flow rate")
mdot_fuel_raw = st.sidebar.text_input("Primary fuel (kg/s)", value="0.38949")  # 예시 값 직접 입력
mdot_air_raw = st.sidebar.text_input("Primary air (kg/s)", value="1.6979")   # 예시 값 직접 입력
mdot_sec_air_raw = st.sidebar.text_input("Secondary air (kg/s)", value="3.9618")

# 1-4. 반응기 형상 및 내부 온도 조건
st.sidebar.subheader("Reactor setting")
psr1_init_T_raw = st.sidebar.text_input("(p) Reaction temperature (K)", value="2000")
# [수정] 부피와 단면적을 text_input으로 변경
psr1_vol_raw = st.sidebar.text_input("(p) Raction volume ($m^3$)", value="0.1")
pfr1_area_raw = st.sidebar.text_input("(p) Combustor cross secion area ($m^2$)", value="0.0314")
pfr1_len_raw = st.sidebar.text_input("dump-secondary (m)", value="0.5")

psr2_vol_raw = st.sidebar.text_input("(s) Reaction volume ($m^3$)", value="0.05")
pfr2_area_raw = st.sidebar.text_input("(s) Combustor cross secion area ($m^2$)", value="0.0314")
pfr2_len_raw = st.sidebar.text_input("secondary-emission probe (m)", value="0.5")

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
    psr1_vol = float(psr1_vol_raw)
    pfr1_area = float(pfr1_area_raw)
    pfr1_len = float(pfr1_len_raw)
    
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
            
            # ----------------------------------------------------
            # [단계 2] PFR 1 계산 (길이 기준 보폭 루프)
            # ----------------------------------------------------
            gas.TPX = psr1.phase.T, psr1.phase.P, psr1.phase.X
            pfr1 = ct.IdealGasConstPressureReactor(gas, clone=False)
            sim_pfr1 = ct.ReactorNet([pfr1])
            
            x_cur = 0.0
            t_cum1 = 0.0
            dx = 0.01
            while x_cur < pfr1_len:
                v = mdot_total_1 / (pfr1.phase.density * pfr1_area)
                t_cum1 += (dx / v)
                sim_pfr1.advance(t_cum1)
                x_cur += dx
                
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
            
            psr2 = ct.IdealGasReactor(gas, clone=False)
            psr2.volume = psr2_vol
            
            mfc_psr2 = ct.MassFlowController(psr2_inlet, psr2, mdot=mdot_total_2)
            valve_2 = ct.Valve(psr2, outlet_2, K=1.0)
            
            sim_psr2 = ct.ReactorNet([psr2])
            sim_psr2.advance_to_steady_state()
            
            tau_psr2 = (psr2.phase.density * psr2.volume) / mdot_total_2
            
            # ----------------------------------------------------
            # [단계 4] PFR 2 계산
            # ----------------------------------------------------
            gas.TPX = psr2.phase.T, psr2.phase.P, psr2.phase.X
            pfr2 = ct.IdealGasConstPressureReactor(gas, clone=False)
            sim_pfr2 = ct.ReactorNet([pfr2])
            
            x_cur2 = 0.0
            t_cum2 = 0.0
            while x_cur2 < pfr2_len:
                v2 = mdot_total_2 / (pfr2.phase.density * pfr2_area)
                t_cum2 += (dx / v2)
                sim_pfr2.advance(t_cum2)
                x_cur2 += dx
            
            # ----------------------------------------------------
            # 📊 결과 리포트 출력 구역
            # ----------------------------------------------------
            st.success("Calculation compeleted")
            
            # 메트릭 카드로 중요 수치 대시보드화
            idx_NO = gas.species_index('NO')
            idx_NO2 = gas.species_index('NO2')
            idx_NH3 = gas.species_index('NH3')
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("Exit temperature", f"{pfr2.phase.T:.1f} K")
            col2.metric("Primary $\phi$", f"{phi1:.4f}")
            col3.metric("Total $\phi$", f"{phi2:.4f}")
            col4.metric("Residence time", f"{(tau_psr1+tau_psr2+t_cum1+t_cum2)*1e3:.2f} ms")
            col5.metric("Exit NOx (NO+NO2)", f"{(pfr2.phase.X[idx_NO]+pfr2.phase.X[idx_NO2])*1e6:.2f} ppm")
            col6.metric("Exit NH3 Slip", f"{pfr2.phase.X[idx_NH3]*1e6:.2f} ppm")
            
            # 표 형태로 상세 데이터 나열
            st.subheader("Data")
            data = {
                "Session": ["Primary reaction", "Post flame zone1", "Secondary reaction", "Emissions probe"],
                "Temperature (K)": [f"{psr1.phase.T:.1f}", f"{pfr1.phase.T:.1f}", f"{psr2.phase.T:.1f}", f"{pfr2.phase.T:.1f}"],
                "Residence time (ms)": [f"{tau_psr1*1e3:.2f}", f"{t_cum1*1e3:.2f}", f"{tau_psr2*1e3:.2f}", f"{t_cum2*1e3:.2f}"],
                "NOx (ppm)": [f"{(psr1.phase.X[idx_NO]+psr1.phase.X[idx_NO2])*1e6:.1f}", f"{(pfr1.phase.X[idx_NO]+pfr1.phase.X[idx_NO2])*1e6:.1f}", f"{(psr2.phase.X[idx_NO]+psr2.phase.X[idx_NO2])*1e6:.1f}", f"{(pfr2.phase.X[idx_NO]+pfr1.phase.X[idx_NO2])*1e6:.1f}"],
                "NH3 (ppm)": [f"{psr1.phase.X[idx_NH3]*1e6:.1f}", f"{pfr1.phase.X[idx_NH3]*1e6:.1f}", f"{psr2.phase.X[idx_NH3]*1e6:.1f}", f"{pfr2.phase.X[idx_NH3]*1e6:.1f}"],
            }
            # st.dataframe(data, use_container_width=True)
            st.dataframe(data, width='stretch')
            
        except Exception as e:
            st.error(f"계산 중 에러가 발생했습니다. 입력 조건을 확인하세요.\n에러 내용: {e}")


# if __name__ == '__main__':
#     import os
#     import sys
#     import subprocess
#     import webbrowser
#     from streamlit.web import cli as stcli

#     # 1. 앱이 실행되면 자동으로 크롬 브라우저로 대시보드 주소 열기
#     webbrowser.open("http://localhost:8501")

#     # 2. PyInstaller 내부 환경에서 Streamlit을 강제로 가동하기
#     sys.argv = ["streamlit", "run", __file__, "--server.port=8501", "--server.headless=true"]
#     sys.exit(stcli.main())
