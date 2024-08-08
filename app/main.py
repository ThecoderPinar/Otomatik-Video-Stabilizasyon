import streamlit as st
import cv2
import os
import base64
import pandas as pd
import plotly.express as px
import threading
import psutil
from video_stabilization import process_video, apply_filters
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit.components.v1 as components

# Sayfa başlığı ve düzeni
st.set_page_config(page_title="Otomatik Video Stabilizasyon Sistemi", layout="wide")

# SQL Server bağlantı bilgileri
server = 'PINAR_DEV\\MSSQLEXPRESS'  # Sunucu adı veya IP adresi
database = 'video_stabilization_db'  # Veritabanı adı

# Bağlantı dizesi (Windows Authentication)
connection_string = f'mssql+pyodbc://@{server}/{database}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server'

# SQLAlchemy motorunu oluşturma
engine = create_engine(connection_string)
Base = declarative_base()

# Geri Bildirim ve Anket Tabloları
class Feedback(Base):
    __tablename__ = 'feedback'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String)
    feedback = sqlalchemy.Column(sqlalchemy.String)


class Survey(Base):
    __tablename__ = 'survey'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    rating = sqlalchemy.Column(sqlalchemy.String)


# Tablo oluşturma
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# CSS dosyasını yükleyin
with open("app/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Menü
st.sidebar.title("Menü")
page = st.sidebar.radio("Git", ["Ana Sayfa", "Proje Bilgileri", "Geliştirici Bilgileri"])

# Sayfa Yönlendirmesi
if page == "Ana Sayfa":
    st.title("🏠 Ana Sayfa")
    st.write("Bu, uygulamanızın ana sayfasıdır.")    # Başlık ve açıklama
    st.markdown('<div class="title">📹 Otomatik Video Stabilizasyon Sistemi</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="description">Bu sistem, titreşimli veya dengesiz çekilmiş videoları otomatik olarak stabilize eder ve netleştirir. Kullanıcılar, elde taşınan kameralarla çekilmiş videoları bile profesyonel bir görünümle izleyebilir hale gelirler.</div>',
        unsafe_allow_html=True
    )

    # Geri Bildirim Formu
    st.sidebar.header("Geri Bildirim Formu")
    name = st.sidebar.text_input("İsminiz")
    email = st.sidebar.text_input("E-posta Adresiniz")
    feedback = st.sidebar.text_area("Geri Bildiriminiz")
    if st.sidebar.button("Gönder"):
        new_feedback = Feedback(name=name, email=email, feedback=feedback)
        session.add(new_feedback)
        session.commit()
        st.sidebar.success("Geri bildirim başarıyla gönderildi!")

    # Anket
    st.sidebar.header("Anket")
    rating = st.sidebar.radio("Bu uygulamayı nasıl değerlendirirsiniz?", ("Harika", "İyi", "Orta", "Kötü"))
    if st.sidebar.button("Anketi Gönder"):
        new_survey = Survey(rating=rating)
        session.add(new_survey)
        session.commit()
        st.sidebar.success("Anket başarıyla gönderildi!")

    # Video yükleme
    uploaded_file = st.file_uploader("Bir video dosyası yükleyin", type=["mp4", "mov", "avi"])

    if uploaded_file is not None:
        input_video_path = os.path.join("demo_videos", uploaded_file.name)
        with open(input_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.video(input_video_path)

        # Filtre seçimi
        filter_option = st.selectbox("Filtre Seçin", ["Yok", "Gri Tonlama", "Sepya"])

        if st.button("Videoyu Stabilize Et ve Netleştir"):
            st.write("İşleniyor, lütfen bekleyin...")
            output_video_path = os.path.join("demo_videos", "stabilized_" + uploaded_file.name)

            processing_time, frame_count, stabilized_video_path = process_video(input_video_path, output_video_path, filter_option)

            st.video(stabilized_video_path)
            st.success("Video başarıyla stabilize edildi ve netleştirildi!")

            st.write(f"📊 İşlenen Kare Sayısı: {frame_count}")
            st.write(f"⏱️ Toplam İşlem Süresi: {processing_time:.2f} saniye")

            # İşlem detaylarını gösteren rapor
            st.subheader("📄 İşlem Raporu")
            report_html = f"""
                <div class="report-container">
                <h2>Video stabilizasyonu ve netleştirme tamamlandı.</h2>
                <p><b>İşlenen video:</b> {uploaded_file.name}</p>
                <p><b>Çıkış video yolu:</b> {output_video_path}</p>
                <p><b>Toplam kare sayısı:</b> {frame_count}</p>
                <p><b>Toplam işlem süresi:</b> {processing_time:.2f} saniye</p>
                <p><b>Ortalama Kare İşlem Süresi:</b> {processing_time / frame_count:.4f} saniye</p>
                <p><b>Video Çözünürlüğü:</b> {stabilized_video_path}</p>
                <p><b>Stabilizasyon Algoritması:</b> Optik Akış</p>
                <p><b>Netleştirme Algoritması:</b> Kenar Geliştirme Filtresi</p>
                </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)

            # Raporu indirme
            report_text = f"""
            Video stabilizasyonu ve netleştirme tamamlandı.
            İşlenen video: {uploaded_file.name}
            Çıkış video yolu: {output_video_path}
            Toplam kare sayısı: {frame_count}
            Toplam işlem süresi: {processing_time:.2f} saniye
            Ortalama Kare İşlem Süresi: {processing_time / frame_count:.4f} saniye
            Video Çözünürlüğü: {stabilized_video_path}
            Stabilizasyon Algoritması: Optik Akış
            Netleştirme Algoritması: Kenar Geliştirme Filtresi
            """

            report_bytes = report_text.encode('utf-8')
            b64 = base64.b64encode(report_bytes).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="stabilization_report.txt">📥 Raporu İndir</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Stabilize edilmiş videoyu indirme
            with open(stabilized_video_path, "rb") as file:
                btn = st.download_button(
                    label="📥 Stabilize Edilmiş Videoyu İndir",
                    data=file,
                    file_name=os.path.basename(stabilized_video_path),
                    mime="video/mp4"
                )

            # Performans grafiği oluşturma
            st.subheader("📊 Performans Grafiği")
            data = {
                'Adım': ['Başlangıç', 'Bitirme'],
                'Süre (saniye)': [0, processing_time],
                'İşlenen Kare Sayısı': [0, frame_count]
            }
            df = pd.DataFrame(data)

            fig1 = px.line(df, x='Adım', y='Süre (saniye)', title='İşlem Süresi Grafiği', markers=True)
            fig2 = px.bar(df, x='Adım', y='İşlenen Kare Sayısı', title='İşlenen Kare Sayısı Grafiği')

            st.plotly_chart(fig1)
            st.plotly_chart(fig2)

            # Sistem Performansı
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            st.write(f"🖥️ CPU Kullanımı: {cpu_usage}%")
            st.write(f"💾 Bellek Kullanımı: {memory_info.percent}%")

elif page == "Proje Bilgileri":
    st.title("📈 Proje Bilgileri")
    st.markdown(
        """
        ## 📹 Otomatik Video Stabilizasyon Sistemi

        Bu proje, titreşimli veya dengesiz çekilmiş videoları otomatik olarak stabilize etmeyi ve netleştirmeyi amaçlamaktadır. 
        Sistem, ardışık kareler arasındaki hareketi hesaplamak için optik akış algoritmalarını kullanır ve stabilize tekniklerini 
        uygulayarak daha düzgün ve sabit bir video üretir. Ayrıca, videoya Gri Tonlama ve Sepya gibi filtreler uygulanabilir.

        ### 🔑 Ana Özellikler:
        - **🎥 Video Stabilizasyonu**: Optik akış kullanarak titreşimli videoları stabilize eder.
        - **✨ Video Netleştirme**: Videodaki kenarları ve detayları geliştirir.
        - **🎨 Filtre Uygulama**: Gri Tonlama ve Sepya filtrelerini uygulamayı destekler.
        - **📊 Performans Metrikleri**: İşlem süresi ve kare sayısı gibi detaylı performans metrikleri sağlar.
        - **📝 Geri Bildirim ve Anket**: Kullanıcı geri bildirimlerini ve derecelendirmelerini toplar.

        ### 🛠️ Kullanım:
        1. 📂 MP4, MOV veya AVI formatında bir video dosyası yükleyin.
        2. 🎛️ Bir filtre seçin (Yok, Gri Tonlama, Sepya).
        3. 🎬 Videoyu işlemek için "Videoyu Stabilize Et ve Netleştir" butonuna tıklayın.
        4. 👀 İşlenen videoyu görüntüleyin ve raporu indirin.

        ### 📝 Örnek Sonuçlar:
        - 🎥 Öncesi ve sonrası stabilizasyon videoları, sistemin etkinliğini göstermek için görüntülenir.
        - 📈 Performans grafikleri, işlem süresi ve işlenen kare sayısı hakkında bilgi sağlar.

        ### 🔍 Kullanılan Yöntemler:
        - **🔄 Optik Akış**: Kareler arasındaki hareketi hesaplamak için.
        - **🔧 Kenar Geliştirme**: Videoyu netleştirmek için.
        - **🗄️ SQLAlchemy**: Geri bildirim ve anket verilerini SQL Server veritabanında saklamak için.
        - **🌐 Streamlit**: Web arayüzünü oluşturmak için.
        """
    )


elif page == "Geliştirici Bilgileri":
    st.title("👩‍💻 Geliştirici Bilgileri")
    st.markdown(
        """
        ## Geliştirici Bilgileri

        **Ad:** Pinar Topuz

        **E-posta:** [piinartp@gmail.com](mailto:piinartp@gmail.com)

        **GitHub:** [github.com/ThecoderPinar](https://github.com/ThecoderPinar)
        """
    )

