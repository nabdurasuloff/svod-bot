RULES=[('Ижтимоий соҳа (таълим, соғлиқни сақлаш)',['pharm','фарм','stom','стом','kardio','кардио',' med ','санитар','sanitar','dorixona','дорихона','maktab','мактаб',"ta'lim","ta`lim",'таълим','shifoxona','шифохона','tibbiyot','тиббиёт','poliklinika','поликлиника','укитувчи','ўқитувчи','oqituvchi','o‘qituvchi','тарбиячи','tarbiyachi','ҳамшира','хамшира','hamshira','bog`cha','bog‘cha','боғча','kollej','коллеж','texnikum','техникум','ijtimoiy','ижтимоий','врач','shifokor','шифокор']),
 ('Қишлоқ хўжалиги',['cluster','clustep','meleratsiya','melior','мелиорац',' fx','fx ','фх',' ф/х','фермер','fermer','qishloq','қишлоқ','agro','агро','chigit','чигит','paxta','пахта','issiqxona','иссиқхона','балиқ','baliq','parranda','парранда','chorva','чорва','klaster','кластер','мавсумий','mavsumiy','dehqon','деҳқон','дехкон','bog‘','bog`','боғбон','агроном','agronom','пилла','pilla']),
 ('Транспорт ва логистика',['transport','транспорт','logist','логист','ҳайдовчи','хайдовчи','haydovchi','avtobus','автобус','temir yo','temiryo','темир йўл','taksi','такси']),
 ('Қурилиш',['build','construct','конструкц','qurilish','қурилиш','курилиш','stroy','строй','бетон','beton','quruvchi','қурувчи','курувчи','ғишт','g‘isht','g`isht','g\'isht','монтаж','montaj','сувоқчи','suvoqchi','arxitekt']),
 ('Савдо',['supply','kompyuter','компютер','savdo','савдо','market','маркет','сотувчи','sotuvchi','kassir','кассир','trade','трейд','do‘kon','do`kon','дўкон','supermarket','magazin','магазин','омбор','ombor']),
 ('Ҳунармандчилик',['hunarmand','ҳунарманд','хунарманд','кулол','kulol','зардўз','zardo','дурадгор','duradgor','заргар','zargar','каштачи','kashtachi','gilam','гилам']),
 ('Саноат (ишлаб чиқариш)',['alyumin','алюмин','alco','алко','mahsulot','maxsulot','маҳсулот','mahsulot','maydalov','майдалов','тахловчи','ўровчи','textil','текстил','tekstil','tikuv','тикув','zavod','завод','fabrika','фабрика','motors','моторс','ceramic','керамик','oyna','ойна','ishlab','ишлаб','sement','цемент','станок','оператор','operator','kabel','кабел','yigiruv','йигирув','mebel','мебел','qadoqlov','қадоқлов','gosht','go`sht','go‘sht','гўшт','sut','сут','jingu','cotton','коттон','industr','индустр','plast','пласт','polimer','полимер','tex','текс','yarn','metall','металл','электрик','elektr','payvand','пайванд','чевар','tikuvchi','тикувчи','non ','нон','qandolat','қандолат','konserva','консерва','tolali','fiber']),
 ('Хизмат кўрсатиш',['obodon','ободон','supuruv','супурув','personnel','taom','таом','kamunal','ta\'mirlash','таъмирлаш','invest','инвест','xizmat','хизмат','service','сервис','oshpaz','ошпаз','ошхона','oshxona','mehmonxona','меҳмонхона','restoran','ресторан','кафе','kafe','сартарош','sartarosh','qorovul','қоровул','коровул','фаррош','farrosh','suv ta','сув таъм','kommunal','коммунал','bank','банк','hokimiyat','ҳокимлик','хокимлик','qo‘riqlash','кўриқлаш','официант','ofitsiant','tozalash','тозалаш','бухгалтер','buxgalter','менежер','menejer','gaz','газ','energ','энерг']),
]
def sect1(emp,pos):
    e=' '+str(emp or '').lower()+' '; p=' '+str(pos or '').lower()+' '
    for txt in (e,p):
        for name,keys in RULES:
            if any(k in txt for k in keys): return name
    return 'Бошқа'
import re as _re
def etype(emp):
    e=' '+str(emp or '').lower()+' '
    if any(k in e for k in (' fx',' fx"','"fx','фх','ф/х','фермер','fermer',' f/x','fx ')): return 'Фермер хўжалиги'
    if any(k in e for k in ('ятт','yatt','якка','yakka','ytt ',' итт')): return 'ЯТТ'
    if any(k in e for k in ('mchj','мчж','ооо','xk','хк',' qk','қк',' ok','aj','аж','dm','дм','mas\'uliyati','mas`uliyati','maktab','мактаб','bo‘limi','бўлими','boshqarma','бошқарма','бошкарма','hokimiyat','ҳокимлик','agentlig','агентлиг','markaz','марказ','xf','davlat','давлат','muassasa','муассаса','korxona','корхона','unitar','унитар','tashkilot','ташкилот','"','«')): return 'МЧЖ/корхона'
    if _re.search(r"(ov|ova|ev|eva|ович|овна|евич|евна|o.g.li|qizi|ўғли|қизи|угли|кизи)\b",e): return 'ЯТТ'
    return 'МЧЖ/корхона'
