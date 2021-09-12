import datetime as dt
import pandas as pd

##GOREV1= VERİYİ ANLAMA VE HAZIRLAMA

#veri setini okutup kopyasını aldık
df_= pd.read_excel("online_retail_II.xlsx")
df= df_.copy()

#veri setinin betimsel istatistiklerine baktık
df.head() #ilk 5 satırı gösterir
df.shape #kaç satır kaç sütun
df.describe() #yüzde çeyrekliklere std mean max gibi değerlere bakar

#hangi veri setinde kaçar tane eksik değişken var
df.isnull().sum()

#eksik değişkenleri çıkardık ve inpalce=true ile kalıcı hale getirdikten sonra tekrar kontrolünü sağladık
df.dropna(inplace=True)
df.isnull().sum()

#değikenler bazında eşsiz ürün sayılarını bulduk
df.nunique()

#hangi üründen kaçar tane olduğunu bulduk
df.groupby("Description").agg({"Quantity": "sum"}).head()
#en çok sipariş edilen 5 ürünü çoktan aza doğru sırala

#en çok sipariş edilen 5 ürünü çoktan aza doğru sıraladık
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head()
                                                                           #ascending=False büyükten küçüğe sıralar
#iptal edilen işlemleri(içerisinde C olan) veri setinden çıkardık
df = df[~df["Invoice"].str.contains("C", na=False)]
       #~ değildir anlamına gelir
df = df[(df['Quantity'] > 0)]
df = df[(df['Price'] > 0)]

#toplam kazancı belirten TotalPrice değişkenini oluşturduk
df["TotalPrice"]= df["Price"] * df["Quantity"]

##GOREV2= RFM METRİKLERİNİN HESAPLANMASI

#Recency, Frequency ve Monetary tanımlarını yaptık
df["InvoiceDate"].max() #faturası en yakın tarihli olan bulunur
today_date= dt.datetime(2011, 12, 11) #bugünün tarihi 2011,12,11 olarak kabul edilir
rfm= df.groupby("Customer ID").agg({"InvoiceDate": lambda InvoiceDate: (today_date- InvoiceDate.max()).days,
                                    "Invoice": lambda Invoice: Invoice.nunique(),
                                    "TotalPrice": lambda TotalPrice: TotalPrice.sum()})
#customer bazında en son kaç gün önce alışveriş yaptığını, unique fatura sayısını ve toplam tutarı hesapladık
rfm.head()
rfm.columns= ["Recency", "Frequency", "Monetary"] #rfm kolon isimlerini yenileriyle değiştirdik
rfm.head() #yeni kolonlar ile ilk 5 değere baktık

#monetary sıfırdan büyük olacak şekilde filtreledik
rfm = rfm[(rfm['Monetary'] > 0)]
rfm.head()

##GOREV3= RFM SKORLARININ OLUŞTURULMASI VE TEK BİR DEĞİŞKENE ÇEVRİLMESİ

#Recency, Frequency ve Monetary metriklerini qcut yardımı ile 1-5 arasında skorlara çeviriniz

rfm["recency_score"]= pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1]) #recency değeri küçük olan max skor puanını alır

rfm["frequency_score"]= pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1,2,3,4,5])

rfm["monetary_score"]= pd.qcut(rfm["Monetary"], 5, labels=[1,2,3,4,5])

rfm["RFM_SCORE"]= (rfm["recency_score"].astype(str) + rfm["frequency_score"].astype(str)) #string olarak skorları birleştirdik

rfm.head()

##GOREV4=  SKORLARIN SEGMEN OLARAK TANIMLANMASI

seg_map = {
    r'[1-2][1-2]': 'hibernating',  #tabloya göre R (1,2), F(1,2) olanları hibernating olarak tanımla
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}
rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
#rfm_score ları seg_mapteki tanımlarla değiştirip regex=True(inplace gibi) ile kalıcı hale getirdik
rfm.head()

rfm[["segment", "Recency", "Frequency", "Monetary"]].groupby("segment").agg(["mean", "count"])

##GOREV_5
# Recency, frequency ve monetary'ye bakıldığında her üç grup için de en önemli olan segment champions segmentidir.
#champions segmenti hem yakın zamanda alışveriş yapmıştır hem de alışveriş sıklığı yüksektir, sık sık alışveriş yapar
#bu yüzden getirisi fazladır. Ancak champions grubundaki müşteri sayısı toplam müşterilere bakıldığında üçüncü sırada
#yer almaktadır. İlk iki sırada hibernating ve loyal customers yer almaktadır. Loyal customers'ı champions segmentine çıkarabilmek
#için adımlar atılmalıdır. Örneğin recency skorunu artırmak için müşterilerin satınaldığı ürünlerin farklı bir renk/modelini satışa çıkarıp
#müşteriye "daha önce ildilendiğiniz şu ürünün mavisi stoklara girdi" gibi mesaj yoluyla müşteriler mağazaya çekilebilir.

#Odaklanılması gereken diğer grup frequency ve monetary açısından ikinci sırada yer alanvcan'loose segmenti olabilir. Can't loose segmenti
#yakın zamanda alışveriş yapmış olmasa da alışveriş yaptığında yüklü miktar harcama yapar ve sıklığı yüksektir. Örneğin
#champions la karşılaştırıldığında champions yaklaşık 10 kat daha fazla müşteriye sahip olmasına rağmen can't loosea göre sadece 1.67 kat
#daha fazla kazandırır, bu sebeple can't loose grubunun recency skoru artırılmaya çalışılıp loyal customers segmentine çıkarma amaçlı aksiyonlar alınmalıdır.
#bu aşamada loyal customers segmentindeki müşteriler ile rastsal bir şekilde birebir görüşmeler yapılıp mağaza hakkındaki görüşleri alınabilir,
#böylece hem loyal customers müşterileri mağazanın kendisine değer verdiğini düşünerek alışveriş yapma isteği ortaya çıkacaktır, hem de
#mağaza loyal customers ın düşüncelerini öğrenip bu etmenleri can't loose segmentindeki müşteriler üzerinde uygulayarak bir üst segmente çıkarabilecektir.

#At risk grubundaki müşterilerin gerekli aksiyonlar alınmazsa hibernating grubuna geçiş yapması çok olasıdır. Bu da %16 lık dilime sahip
# olan at risk grubundaki müşterileri kaybetmek demektir. Bunu önlemek için bu gruba da öncelik verilmelidir. Mümkünse loyal customers segmentine
#en kötü ihtimalle ise need attention segmentine çıkarılması üzerine çalışmalar yapılmalıdır. Hibernating segmentine düşmemesi için alışveriş frekansını aynı seviyede tutup
# recency skorunu artırma üzerine çalışmalar yapılmalıdır. Müşteriler bir an önce mağazaya çekilmelidir. Bu müşteriler aynı veya benzer
#ürünü daha uygun fiyata başka bir mağazada bulmuş olabilir, champions ile karşılaştırıldığında aynı kişi sayısına sahip olmalarına rağmen
#frekans değeri monetary ile orantılandığında daha az para harcadığı ve dolayısıyla ürünlerin fiyatına daha çok önem verdiği görülmektedir.
# Bu müşterilerin düzenli olarak satınaldığı belirli ürünleri pazar araştırmasına göre "şimdi şu ürünü %40 daha uygun fiyata satın alabilirsiniz"
# gibi pazarlama teknikleri kullanılabilir.