def sec(a):
    t=a.lower()
    K=[('Ижтимоий соҳа (таълим, соғлиқни сақлаш)',['bolalarga qarab','bemorlarga','hamshira','nogiron','oilaviy bolalar uyi','xalq tabobati','konsultatsiya','trener','sport toʻgarak']),
       ('Транспорт ва логистика',['avtotransport','yuk tashish','yetkazib berish','aravada','yuk ortish']),
       ('Қурилиш',['santexnika','elektr montaj','gips','landshaft','tosh va tosh']),
       ('Қишлоқ хўжалиги',['chorva','tomorqa','issiqxona','qishloq','xonaki tovuq','asalari','sut va sut','ekin ekish','pilla','supurgi yetishtir','artemiya','qo‘ziqorin','qo\'ziqorin','jun yi','junni yig','teri xomashyo','fermer','uy hayvonlari']),
       ('Савдо',['savdo','oldi sotdisi','vositachilik','sotish','chakana','etiketka']),
       ('Ҳунармандчилик',['non va patir','ko‘ylak tikish','quroqchilik','atlas','munchoq','temirchilik','taqinchoq','yog‘och','yog`och','o‘yinchog‘','do‘ppi','dag‘al jun','qayta ishlangan jun','kandakorlik','kulolchilik','tandir','pichoq','qog‘ozdan','rassomlik','charxlash','kalitlar','tikish']),
       ('Хизмат кўрсатиш',['uy ishlarini','avtomobil yuvish','kompyuter','velosiped','ta\'mirlash','ta’mirlash','poyabzal','ma\'ishiy','musiqa asboblari','konserj','dasturiy','multimedia','ijtimoiy tarmoq','kibersport','kadr tanlash','suratga','o\'lchov','taksidermik','nomoddiy','stipendiya'])]
    for s,ks in K:
        if any(k in t for k in ks): return s
    return 'Бошқа'
