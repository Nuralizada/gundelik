import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar  # Ayın gün sayını hesablamaq üçün

# Tətbiq üçün konfiqurasiya
st.set_page_config(page_title="Gündəlik Hesabat", layout="wide")

# **Səhifələr arasında keçid üçün yan menyu**
page = st.sidebar.selectbox("Səhifəni seçin", ["Report", "Current Month", "Current Year" ])

# Cari tarix məlumatları
current_date = pd.Timestamp.today()
current_month = current_date.month
current_year = current_date.year

# CSS ilə dashboard tərtibatı üçün stilizasiya edirik
dashboard_style = """
    <style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
        color: #004AAD;
        text-align: center;
    }
    .metric-box {
        border-radius: 8px;
        padding: 20px;
        background-color: #F0F2F6;
        text-align: center;
        margin: 0 10px;
        width: 200px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .card-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    </style>
"""
# HTML tərzini səhifəyə əlavə edirik
st.markdown(dashboard_style, unsafe_allow_html=True)

# Məlumatların yüklənməsi
fact_url = 'https://drive.google.com/uc?id=1LTo-lDhJy6-AMxHpX-B-o_8t7-qmoT2M&export=download'

fakt_df = pd.read_csv(fact_url)

file_path = "plan fakt.xlsx"
plan_df = pd.read_excel(file_path)

# Lazım olan sütunların seçilməsi
plan_columns = ['Rejim', 'Ekspeditor', 'Əsas yük', 'Tarix', 'plan hecm','Vaqon/konteyner']
plan_df_selected = plan_df[plan_columns]

fakt_columns = ['əsas_yüklər', 'Rejim', 'Eksp', 'Həcm_fakt', 'Tarix','vaqon_növü','GSA','Göndərən ölkə','Vaqon_sayı']
fakt_df_selected = fakt_df[fakt_columns]

# Tarix sütunlarının datetime formatına çevrilməsi
plan_df_selected['Tarix'] = pd.to_datetime(plan_df_selected['Tarix'], errors='coerce')
fakt_df_selected['Tarix'] = pd.to_datetime(fakt_df_selected['Tarix'], errors='coerce')

if page == "Report":
    # Dashboard başlığı
    st.markdown("<h1 style='text-align: center; color: #004AAD;'>Gündəlik Hesabat</h1>", unsafe_allow_html=True)

    # Filterləri yan-yana yerləşdirmək üçün columns() istifadə edirik
    col1, col2 = st.columns(2)

    with col1:
        # Tarix filterini fakt datasındakı tarixlərə əsasən hazırlayırıq
        available_dates = fakt_df_selected['Tarix'].dt.date.unique()
        available_dates = sorted(available_dates)

        selected_date = st.selectbox('Tarix', available_dates)

        selected_date = pd.to_datetime(selected_date)

        # Seçilmiş tarixə əsasən ayı və ili müəyyən edirik
        selected_month = selected_date.month
        selected_year = selected_date.year

        # Ayın gün sayını hesablayırıq
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]

        # Seçilmiş gün sayı
        selected_day = selected_date.day

    with col2:
        # Rejimlər üçün unikal dəyərləri əldə edirik
        rejimler_plan = plan_df_selected['Rejim'].unique()
        rejimler_fakt = fakt_df_selected['Rejim'].unique()
        rejimler = list(set(rejimler_plan) | set(rejimler_fakt))

        # Rejimləri seçmək üçün multiselect
        selected_rejim = st.multiselect('Rejimi', rejimler, default=rejimler)

    # Plan datasını seçilmiş aya və ilə görə filtr edirik
    plan_df_filtered = plan_df_selected[
        (plan_df_selected['Tarix'].dt.month == selected_month) &
        (plan_df_selected['Tarix'].dt.year == selected_year)
    ]

    # Əgər plan datası boşdursa, xəbərdarlıq veririk
    if plan_df_filtered.empty:
        st.warning("Seçilmiş tarix üçün plan məlumatları tapılmadı.")
    else:
        # Plan həcmlərini gün sayına görə tənzimləyirik
        plan_df_filtered['plan hecm'] = (plan_df_filtered['plan hecm'] / days_in_month) * selected_day

    # Fakt datasını seçilmiş tarixə qədər filtr edirik (ayın əvvəlindən seçilmiş tarixə qədər)
    start_of_month = pd.to_datetime(f'{selected_year}-{selected_month}-01')
    fakt_df_filtered = fakt_df_selected[
        (fakt_df_selected['Tarix'] >= start_of_month) & 
        (fakt_df_selected['Tarix'] <= selected_date)
    ]

    # 'Rejim' sütunundakı NaN dəyərləri silirik
    plan_df_filtered = plan_df_filtered.dropna(subset=['Rejim'])
    fakt_df_filtered = fakt_df_filtered.dropna(subset=['Rejim'])

    # Seçilmiş rejimlərə görə filtrasiyanı aparırıq
    plan_df_filtered = plan_df_filtered[plan_df_filtered['Rejim'].isin(selected_rejim)]
    fakt_df_filtered = fakt_df_filtered[fakt_df_filtered['Rejim'].isin(selected_rejim)]

    # DataFrame-lərin boş olub olmadığını yoxlayırıq
    if plan_df_filtered.empty and fakt_df_filtered.empty:
        st.warning("Seçilmiş filtrasiya nəticəsində data tapılmadı.")
    else:
        # **Ümumi Kartlar üçün məbləğlərin hesablanması**
        total_plan = plan_df_filtered['plan hecm'].sum()
        total_fact = fakt_df_filtered['Həcm_fakt'].sum()
        if total_plan == 0:
            total_percentage = 0
        else:
            total_percentage = (total_fact / total_plan) * 100

        # Rəqəmləri formatlayırıq
        total_plan_formatted = "{:,.0f}".format(total_plan)
        total_fact_formatted = "{:,.0f}".format(total_fact)
        total_percentage_formatted = "{:,.0f}%".format(total_percentage)

        # **Ümumi Kartları stilizə edərək ortada yaradırıq**
        st.markdown("""
            <div class="card-container">
                <div class="metric-box">
                    <div class="big-font">Plan</div>
                    <div class="big-font">{}</div>
                </div>
                <div class="metric-box">
                    <div class="big-font">Fakt</div>
                    <div class="big-font">{}</div>
                </div>
                <div class="metric-box">
                    <div class="big-font">Yerinə Yetirmə Faizi</div>
                    <div class="big-font">{}</div>
                </div>
            </div>
        """.format(total_plan_formatted, total_fact_formatted, total_percentage_formatted), unsafe_allow_html=True)

        # **Rejimlər üzrə Kartların yaradılması (Rejim filterindən asılı olmadan)**
        plan_by_rejim = plan_df_selected.groupby('Rejim')['plan hecm'].sum().reset_index()
        fakt_by_rejim = fakt_df_selected.groupby('Rejim')['Həcm_fakt'].sum().reset_index()

        # Datasları birləşdiririk
        merged_rejim = pd.merge(plan_by_rejim, fakt_by_rejim, on='Rejim', how='outer')

        # NaN dəyərləri 0 ilə əvəz edirik
        merged_rejim['plan hecm'] = merged_rejim['plan hecm'].fillna(0)
        merged_rejim['Həcm_fakt'] = merged_rejim['Həcm_fakt'].fillna(0)

        # Faiz dəyərlərinin hesablanması
        def calculate_percentage(row):
            if row['plan hecm'] == 0:
                return 0
            else:
                return (row['Həcm_fakt'] / row['plan hecm']) * 100

        merged_rejim['Faiz'] = merged_rejim.apply(calculate_percentage, axis=1)

        # Rəqəmləri formatlayırıq
        merged_rejim['Faiz_formatted'] = merged_rejim['Faiz'].apply(lambda x: "{:,.0f}%".format(x))

        # Rejimlər üzrə faizləri əldə edirik
        tranzit_faiz = merged_rejim.loc[merged_rejim['Rejim'] == 'Tranzit', 'Faiz_formatted'].values
        idxal_faiz = merged_rejim.loc[merged_rejim['Rejim'] == 'İdxal', 'Faiz_formatted'].values
        ixrac_faiz = merged_rejim.loc[merged_rejim['Rejim'] == 'İxrac', 'Faiz_formatted'].values
        daxili_faiz = merged_rejim.loc[merged_rejim['Rejim'] == 'Daxili', 'Faiz_formatted'].values

        # Əgər dəyərlər mövcud deyilsə, 0% olaraq təyin edirik
        tranzit_faiz = tranzit_faiz[0] if len(tranzit_faiz) > 0 else '0%'
        idxal_faiz = idxal_faiz[0] if len(idxal_faiz) > 0 else '0%'
        ixrac_faiz = ixrac_faiz[0] if len(ixrac_faiz) > 0 else '0%'
        daxili_faiz = daxili_faiz[0] if len(daxili_faiz) > 0 else '0%'

        # **Rejimlər üzrə Kartları yaradaraq göstəririk**
        st.markdown("""
            <div class="card-container">
                <div class="metric-box">
                    <div class="big-font">Tranzit</div>
                    <div class="big-font">{}</div>
                </div>
                <div class="metric-box">
                    <div class="big-font">İdxal</div>
                    <div class="big-font">{}</div>
                </div>
                <div class="metric-box">
                    <div class="big-font">İxrac</div>
                    <div class="big-font">{}</div>
                </div>
                <div class="metric-box">
                    <div class="big-font">Daxili</div>
                    <div class="big-font">{}</div>
                </div>
            </div>
        """.format(tranzit_faiz, idxal_faiz, ixrac_faiz, daxili_faiz), unsafe_allow_html=True)

        # Dashboard üslubu kartlar və qrafiklər
        st.markdown("---")  # Qrafiklərdən öncə xətt

        # Plan datasını qruplaşdırırıq
        plan_grouped = plan_df_filtered.groupby('Ekspeditor')['plan hecm'].sum().reset_index()

        # Fakt datasını qruplaşdırırıq
        fakt_grouped = fakt_df_filtered.groupby('Eksp')['Həcm_fakt'].sum().reset_index()
        fakt_grouped.rename(columns={'Eksp': 'Ekspeditor'}, inplace=True)

        # Datasları birləşdiririk
        merged_df = pd.merge(plan_grouped, fakt_grouped, on='Ekspeditor', how='outer')

        # NaN dəyərləri 0 ilə əvəz edirik
        merged_df['plan hecm'] = merged_df['plan hecm'].fillna(0)
        merged_df['Həcm_fakt'] = merged_df['Həcm_fakt'].fillna(0)

        # Faiz dəyərlərinin hesablanması
        def calculate_percentage(row):
            if row['plan hecm'] == 0:
                return 0
            else:
                return (row['Həcm_fakt'] / row['plan hecm']) * 100

        merged_df['Faiz'] = merged_df.apply(calculate_percentage, axis=1)

        # Rəqəmləri minlik ayırıcısı ilə formatlayırıq
        merged_df['plan hecm_formatted'] = merged_df['plan hecm'].apply(lambda x: "{:,.0f}".format(x))
        merged_df['Həcm_fakt_formatted'] = merged_df['Həcm_fakt'].apply(lambda x: "{:,.0f}".format(x))
        merged_df['Faiz_formatted'] = merged_df['Faiz'].apply(lambda x: "{:,.0f}%".format(x))

        # **Cədvəl üçün sütunları və dəyərləri hazırlayırıq**
        header_values = ['Ekspeditor', 'Plan Həcmi', 'Fakt Həcmi', 'Faiz (%)']
        cell_values = [merged_df['Ekspeditor'],
                    merged_df['plan hecm_formatted'],
                    merged_df['Həcm_fakt_formatted'],
                    merged_df['Faiz_formatted']]

        fig_table = go.Figure(data=[go.Table(
            header=dict(values=header_values,
                        fill_color='#004AAD',
                        font=dict(color='white', size=12),
                        align='center'),
            cells=dict(values=cell_values,
                    fill_color=[['#F0F2F6'] * len(merged_df['Ekspeditor'])],
                    align='center',
                    font=dict(size=11))
        )])

        # Plotly cədvəlini göstəririk
        st.plotly_chart(fig_table)

        # **Qrafik - Plan vs Fakt**:
        st.markdown("<h4 style='color:#1b2a85;'>Ekspeditorlar üzrə ümumi daşınma göstəriciləri</h4>", unsafe_allow_html=True)

        fig_plan_fact = go.Figure(data=[
            go.Bar(name='Plan', x=merged_df['Ekspeditor'], y=merged_df['plan hecm'], marker_color='#263066', 
                text=merged_df['plan hecm_formatted'], textposition='outside'),
            go.Bar(name='Fakt', x=merged_df['Ekspeditor'], y=merged_df['Həcm_fakt'], marker_color='#a2b0fc',
                text=merged_df['Həcm_fakt_formatted'], textposition='outside')
        ])
        
        fig_plan_fact.update_layout(barmode='group',  template="plotly_white")
        st.plotly_chart(fig_plan_fact)





elif page == "Current Month":
    st.markdown("<h1 style='text-align: center; color: #e0392d;'>Rejimlər üzrə aylıq göstəricilər</h1>", unsafe_allow_html=True)

    # Filterləri yan-yana yerləşdirmək üçün columns() istifadə edirik
    col1, col2 = st.columns(2)

    with col1:
        # Tarix filterini fakt datasındakı bütün tarixlərə əsasən hazırlayırıq
        available_dates = fakt_df_selected['Tarix'].dt.date.unique()
        available_dates = sorted(available_dates)

        selected_date = st.selectbox('', available_dates)

        selected_date = pd.to_datetime(selected_date)

    with col2:
        # Rejimlər üçün unikal dəyərləri əldə edirik
        rejimler_plan = plan_df_selected['Rejim'].unique()
        rejimler_fakt = fakt_df_selected['Rejim'].unique()
        rejimler = list(set(rejimler_plan) | set(rejimler_fakt))
        rejimler = sorted(rejimler)

        # Rejim filterini selectbox kimi yaradırıq
        selected_rejim = st.selectbox('', rejimler)

    # Data filtrasiyası
    # Plan datasını seçilmiş ay və ilə görə filtr edirik
    plan_df_filtered = plan_df_selected[
        (plan_df_selected['Tarix'].dt.month == selected_date.month) &
        (plan_df_selected['Tarix'].dt.year == selected_date.year) &
        (plan_df_selected['Rejim'] == selected_rejim)
    ]

    # Fakt datasını ayın əvvəli ilə seçilmiş tarix arasında və seçilmiş rejimə görə filtr edirik
    start_of_month = pd.to_datetime(f'{selected_date.year}-{selected_date.month}-01')

    fakt_df_filtered = fakt_df_selected[
        (fakt_df_selected['Tarix'] >= start_of_month) &
        (fakt_df_selected['Tarix'] <= selected_date) &
        (fakt_df_selected['Rejim'] == selected_rejim)
    ]

    # Plan həcmini seçilmiş tarixə uyğun tənzimləmək üçün
    if not plan_df_filtered.empty:
        # Ayın gün sayını və seçilmiş günü hesablayırıq
        days_in_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
        selected_day = selected_date.day

        # Plan həcmini tənzimləyirik
        plan_df_filtered['plan hecm'] = (plan_df_filtered['plan hecm'] / days_in_month) * selected_day
    else:
        plan_df_filtered['plan hecm'] = 0

    # Fakt həcmini hesablayırıq
    total_fact = fakt_df_filtered['Həcm_fakt'].sum()
    total_plan = plan_df_filtered['plan hecm'].sum()

    # Yerinə yetirmə faizini hesablayırıq
    if total_plan == 0:
        total_percentage = 0
    else:
        total_percentage = (total_fact / total_plan) * 100

    # Rəqəmləri formatlayırıq
    total_plan_formatted = "{:,.0f}".format(total_plan)
    total_fact_formatted = "{:,.0f}".format(total_fact)
    total_percentage_formatted = "{:,.0f}%".format(total_percentage)

    # **Ümumi Kartları stilizə edərək ortada yaradırıq**
    st.markdown("""
        <div class="card-container">
            <div class="metric-box">
                <div class="big-font">Plan</div>
                <div class="big-font">{}</div>
            </div>
            <div class="metric-box">
                <div class="big-font">Fakt</div>
                <div class="big-font">{}</div>
            </div>
            <div class="metric-box">
                <div class="big-font">Yerinə Yetirmə Faizi</div>
                <div class="big-font">{}</div>
            </div>
        </div>
    """.format(total_plan_formatted, total_fact_formatted, total_percentage_formatted), unsafe_allow_html=True)

    # **Məhsullar üzrə Plan və Fakt Həcm Cədvəlinin Yaradılması**

    # Plan datasında 'Əsas yük' sütununu 'Məhsul' olaraq adlandırırıq
    plan_df_filtered = plan_df_filtered.rename(columns={'Əsas yük': 'Məhsul'})

    # Fakt datasında 'əsas_yüklər' sütununu 'Məhsul' olaraq adlandırırıq
    fakt_df_filtered = fakt_df_filtered.rename(columns={'əsas_yüklər': 'Məhsul'})

    # Məhsul üzrə plan həcmlərini hesablayırıq
    plan_by_product = plan_df_filtered.groupby('Məhsul')['plan hecm'].sum().reset_index()

    # Məhsul üzrə fakt həcmlərini hesablayırıq
    fakt_by_product = fakt_df_filtered.groupby('Məhsul')['Həcm_fakt'].sum().reset_index()

    # Plan və fakt datasını məhsul üzrə birləşdiririk
    merged_product = pd.merge(plan_by_product, fakt_by_product, on='Məhsul', how='outer')

    # NaN dəyərləri 0 ilə əvəz edirik
    merged_product['plan hecm'] = merged_product['plan hecm'].fillna(0)
    merged_product['Həcm_fakt'] = merged_product['Həcm_fakt'].fillna(0)

    # **Sıralama tətbiq edirik (plan həcmi və fakt həcmi üzrə çoxdan aza doğru)**
    merged_product['total'] = merged_product['plan hecm'] + merged_product['Həcm_fakt']
    merged_product = merged_product.sort_values(by=['total'], ascending=False).reset_index(drop=True)
    merged_product = merged_product.drop('total', axis=1)

    # **'Digər yüklər' sətrini ən aşağı yerləşdiririk**
    if 'Digər yüklər' in merged_product['Məhsul'].values:
        # 'Digər yüklər' sətrini seçirik
        other_row = merged_product[merged_product['Məhsul'] == 'Digər yüklər']
        # Qalan sətrləri seçirik
        rest_rows = merged_product[merged_product['Məhsul'] != 'Digər yüklər']
        # Qalan sətrləri birləşdiririk və 'Digər yüklər' sətrini ən sona əlavə edirik
        merged_product = pd.concat([rest_rows, other_row], ignore_index=True)

    # Yerinə yetirmə faizini hesablayırıq
    merged_product['Faiz'] = merged_product.apply(
        lambda row: (row['Həcm_fakt'] / row['plan hecm']) * 100 if row['plan hecm'] != 0 else 0, axis=1)

    # Rəqəmləri formatlayırıq
    merged_product['plan hecm_formatted'] = merged_product['plan hecm'].apply(lambda x: "{:,.0f}".format(x))
    merged_product['Həcm_fakt_formatted'] = merged_product['Həcm_fakt'].apply(lambda x: "{:,.0f}".format(x))
    merged_product['Faiz_formatted'] = merged_product['Faiz'].apply(lambda x: "{:,.0f}%".format(x))

    # **Məhsullar üzrə cədvəli göstəririk**
    st.markdown("<h3 style='text-align: center; color: #004AAD;'>Yüklər üzrə plan və fakt</h3>", unsafe_allow_html=True)

    # Cədvəl üçün sütunları və dəyərləri hazırlayırıq
    header_values_product = ['Məhsul', 'Plan Həcmi', 'Fakt Həcmi', 'Faiz (%)']
    cell_values_product = [merged_product['Məhsul'],
                           merged_product['plan hecm_formatted'],
                           merged_product['Həcm_fakt_formatted'],
                           merged_product['Faiz_formatted']]

    fig_table_product = go.Figure(data=[go.Table(
        columnwidth=[200, 100, 100, 80],
        header=dict(
            values=header_values_product,
            fill_color='#004AAD',
            font=dict(color='white', size=14, family='Arial'),
            align='center'
        ),
        cells=dict(
            values=cell_values_product,
            fill_color=[['#F0F2F6'] * len(merged_product)],
            align='center',
            font=dict(color='black', size=12, family='Arial')
        )
    )])

    # Cədvəlin ölçüsünü artırırıq
    fig_table_product.update_layout(
        width=800,
        height=600
    )

    # Plotly cədvəlini göstəririk
    st.plotly_chart(fig_table_product)

    # **Ekspeditorlar üzrə Plan və Fakt Həcm Cədvəlinin Yaradılması**

    # Fakt datasında 'Eksp' sütununu 'Ekspeditor' olaraq adlandırırıq
    fakt_df_filtered = fakt_df_filtered.rename(columns={'Eksp': 'Ekspeditor'})

    # Plan datasında 'Ekspeditor' sütunu varsa, yoxlayırıq
    if 'Ekspeditor' not in plan_df_filtered.columns:
        plan_df_filtered['Ekspeditor'] = 'Naməlum'

    # Ekspeditor üzrə plan həcmlərini hesablayırıq
    plan_by_ekspeditor = plan_df_filtered.groupby('Ekspeditor')['plan hecm'].sum().reset_index()

    # Ekspeditor üzrə fakt həcmlərini hesablayırıq
    fakt_by_ekspeditor = fakt_df_filtered.groupby('Ekspeditor')['Həcm_fakt'].sum().reset_index()

    # Plan və fakt datasını ekspeditor üzrə birləşdiririk
    merged_ekspeditor = pd.merge(plan_by_ekspeditor, fakt_by_ekspeditor, on='Ekspeditor', how='outer')

    # NaN dəyərləri 0 ilə əvəz edirik
    merged_ekspeditor['plan hecm'] = merged_ekspeditor['plan hecm'].fillna(0)
    merged_ekspeditor['Həcm_fakt'] = merged_ekspeditor['Həcm_fakt'].fillna(0)

    # **Sıralama tətbiq edirik (plan həcmi və fakt həcmi üzrə çoxdan aza doğru)**
    merged_ekspeditor['total'] = merged_ekspeditor['plan hecm'] + merged_ekspeditor['Həcm_fakt']
    merged_ekspeditor = merged_ekspeditor.sort_values(by=['total'], ascending=False).reset_index(drop=True)
    merged_ekspeditor = merged_ekspeditor.drop('total', axis=1)

    # Yerinə yetirmə faizini hesablayırıq
    merged_ekspeditor['Faiz'] = merged_ekspeditor.apply(
        lambda row: (row['Həcm_fakt'] / row['plan hecm']) * 100 if row['plan hecm'] != 0 else 0, axis=1)

    # Rəqəmləri formatlayırıq
    merged_ekspeditor['plan hecm_formatted'] = merged_ekspeditor['plan hecm'].apply(lambda x: "{:,.0f}".format(x))
    merged_ekspeditor['Həcm_fakt_formatted'] = merged_ekspeditor['Həcm_fakt'].apply(lambda x: "{:,.0f}".format(x))
    merged_ekspeditor['Faiz_formatted'] = merged_ekspeditor['Faiz'].apply(lambda x: "{:,.0f}%".format(x))

    # **Ekspeditorlar üzrə cədvəli göstəririk**
    st.markdown("<h3 style='text-align: center; color: #004AAD;'>Ekspeditorlar üzrə plan və fakt</h3>", unsafe_allow_html=True)

    # Cədvəl üçün sütunları və dəyərləri hazırlayırıq
    header_values_ekspeditor = ['Ekspeditor', 'Plan Həcmi', 'Fakt Həcmi', 'Faiz (%)']
    cell_values_ekspeditor = [merged_ekspeditor['Ekspeditor'],
                              merged_ekspeditor['plan hecm_formatted'],
                              merged_ekspeditor['Həcm_fakt_formatted'],
                              merged_ekspeditor['Faiz_formatted']]

    fig_table_ekspeditor = go.Figure(data=[go.Table(
        columnwidth=[200, 100, 100, 80],
        header=dict(
            values=header_values_ekspeditor,
            fill_color='#004AAD',
            font=dict(color='white', size=14, family='Arial'),
            align='center'
        ),
        cells=dict(
            values=cell_values_ekspeditor,
            fill_color=[['#F0F2F6'] * len(merged_ekspeditor)],
            align='center',
            font=dict(color='black', size=12, family='Arial')
        )
    )])

    # Cədvəlin ölçüsünü artırırıq
    fig_table_ekspeditor.update_layout(
        width=800,
        height=600
    )

    # Plotly cədvəlini göstəririk
    st.plotly_chart(fig_table_ekspeditor)

    # **Vaqon/Konteyner üzrə Plan və Fakt Həcm Cədvəlinin Yaradılması**

    # Plan datasında 'Vaqon/konteyner' sütununu 'vaqon_növü' olaraq adlandırırıq
    plan_df_filtered = plan_df_filtered.rename(columns={'Vaqon/konteyner': 'vaqon_növü'})

    # Fakt datasında 'vaqon_növü' sütunu artıq mövcuddur

    # Plan datasında plan həcmini seçilmiş tarixə uyğun tənzimləyirik
    if not plan_df_filtered.empty:
        plan_df_filtered['plan hecm'] = (plan_df_filtered['plan hecm'] / days_in_month) * selected_day
    else:
        plan_df_filtered['plan hecm'] = 0

    # Vaqon_növü üzrə plan həcmlərini hesablayırıq
    plan_by_vaqon = plan_df_filtered.groupby('vaqon_növü')['plan hecm'].sum().reset_index()

    # Vaqon_növü üzrə fakt həcmlərini hesablayırıq
    fakt_by_vaqon = fakt_df_filtered.groupby('vaqon_növü')['Həcm_fakt'].sum().reset_index()

    # Plan və fakt datasını vaqon_növü üzrə birləşdiririk
    merged_vaqon = pd.merge(plan_by_vaqon, fakt_by_vaqon, on='vaqon_növü', how='outer')

    # NaN dəyərləri 0 ilə əvəz edirik
    merged_vaqon['plan hecm'] = merged_vaqon['plan hecm'].fillna(0)
    merged_vaqon['Həcm_fakt'] = merged_vaqon['Həcm_fakt'].fillna(0)

    # **Sıralama tətbiq edirik (plan həcmi və fakt həcmi üzrə çoxdan aza doğru)**
    merged_vaqon['total'] = merged_vaqon['plan hecm'] + merged_vaqon['Həcm_fakt']
    merged_vaqon = merged_vaqon.sort_values(by=['total'], ascending=False).reset_index(drop=True)
    merged_vaqon = merged_vaqon.drop('total', axis=1)

    # Yerinə yetirmə faizini hesablayırıq
    merged_vaqon['Faiz'] = merged_vaqon.apply(
        lambda row: (row['Həcm_fakt'] / row['plan hecm']) * 100 if row['plan hecm'] != 0 else 0, axis=1)

    # Rəqəmləri formatlayırıq
    merged_vaqon['plan hecm_formatted'] = merged_vaqon['plan hecm'].apply(lambda x: "{:,.0f}".format(x))
    merged_vaqon['Həcm_fakt_formatted'] = merged_vaqon['Həcm_fakt'].apply(lambda x: "{:,.0f}".format(x))
    merged_vaqon['Faiz_formatted'] = merged_vaqon['Faiz'].apply(lambda x: "{:,.0f}%".format(x))

    # **Vaqon/Konteyner üzrə cədvəli göstəririk**
    st.markdown("<h3 style='text-align: center; color: #004AAD;'>Vaqon/Konteyner üzrə plan və fakt</h3>", unsafe_allow_html=True)

    # Cədvəl üçün sütunları və dəyərləri hazırlayırıq
    header_values_vaqon = ['Vaqon/Konteyner', 'Plan Həcmi', 'Fakt Həcmi', 'Faiz (%)']
    cell_values_vaqon = [merged_vaqon['vaqon_növü'],
                         merged_vaqon['plan hecm_formatted'],
                         merged_vaqon['Həcm_fakt_formatted'],
                         merged_vaqon['Faiz_formatted']]

    fig_table_vaqon = go.Figure(data=[go.Table(
        columnwidth=[200, 100, 100, 80],
        header=dict(
            values=header_values_vaqon,
            fill_color='#004AAD',
            font=dict(color='white', size=14, family='Arial'),
            align='center'
        ),
        cells=dict(
            values=cell_values_vaqon,
            fill_color=[['#F0F2F6'] * len(merged_vaqon)],
            align='center',
            font=dict(color='black', size=12, family='Arial')
        )
    )])

    # Cədvəlin ölçüsünü artırırıq
    fig_table_vaqon.update_layout(
        width=800,
        height=600
    )

    # Plotly cədvəlini göstəririk
    st.plotly_chart(fig_table_vaqon)
    
    






