#-*- coding: utf-8 -*-
from scrapy.loader import ItemLoader
from EEMovel import items
import scrapy
# from scrapy_splash import SplashRequest

class Spider(scrapy.Spider):
    name = 'brasilbrokers'
    start_urls = ['https://brasilbrokers.com.br/imoveis/load-lista']
    lista_url = []
    qtd_imoveis = 0
    cidade_imobiliaria = 'Rio de Janeiro'
    contato_imobiliaria = '(21) 2112-1013'
    email_imobiliaria = 'atendimentorj@vendasbb.com.br'
    uf_imobiliaria = 'RJ'
    bairro_imobiliaria = 'Barra da Tijuca'
    cidade_imobiliaria = 'Rio de Janeiro'
    endereco_imobiliaria = 'Avenida das Américas , 3443 Bloco 3 - Sala 102/103'
    creci = 'CJ 5680'
    
    
    custom_settings = {
        'DOWNLOAD_DELAY':1, 
        'USER_AGENT':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
        }
    def start_requests(self):
        
        cidades = {
            'Areal - RJ':{'ordem':'2','valor_busca':'9E7EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Cachoeiras de Macacu - RJ':{'ordem':'2','valor_busca':'B97EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Angra dos Reis - RJ':{'ordem':'2','valor_busca':'9A7EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Belford Roxo - RJ':{'ordem':'2','valor_busca':'AF7EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Armação dos Búzios - RJ':{'ordem':'2','valor_busca':'9F7EFAEB-84F7-DF11-8BFA-02BFC0A80045'},	
            'Arraial do Cabo - RJ':{'ordem':'2','valor_busca':'A07EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Araruama - RJ':{'ordem':'2','valor_busca':'9A7EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Cabo Frio - RJ':{'ordem':'2','valor_busca':'B77EFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Niterói - RJ':{'ordem':'1','valor_busca':'2F7FFAEB-84F7-DF11-8BFA-02BFC0A80045'},
            'Rio de Janeiro - RJ':{'ordem':'0','valor_busca':'647FFAEB-84F7-DF11-8BFA-02BFC0A80045'}
            }

        for i in cidades:
            
            cidade = i
            ordem = cidades[i]["ordem"]
            valor_busca = cidades[i]["valor_busca"]

            formdata = {
                'Busca': cidade,
                'Ordem': ordem,
                'PageCount': '0',
                'PageSize': '1000',
                'TipoBusca': 'C',
                'TipoLaudo': '4',
                'Uf': 'c59cca80-84f7-df11-8bfa-02bfc0a80045',
                'ValorBusca': valor_busca,
                'Page': '1'
                }
            
            req = scrapy.FormRequest(url='https://brasilbrokers.com.br/imoveis/load-lista', method='POST', formdata=formdata, callback=self.parse)
            req.meta['formdata'] = formdata
            req.meta['valor_busca'] = valor_busca
            req.meta['ordem'] = ordem
            req.meta['Busca'] = cidade,
            req.meta['pagina'] = 1
            yield req
       

    def parse(self, response):
 
        items = response.xpath('//div[@class="col-12 col-lg-6 col-xl-4 pb-3 px-2 imovel-container"]')
        
        for item in items:
            url = 'https://brasilbrokers.com.br' + item.xpath('./a/@href').extract_first()
            if 'prontos' in url:
                req = scrapy.Request(url=url, callback=self.parse_detail)    
                yield req
            else:
                pass
 
        if len(items) == 1000: #pagesize from formdata
            pagina = response.meta['pagina']
            pagina += 1
            formdata = response.meta["formdata"]
            formdata["Page"] = str(pagina)
            req= scrapy.FormRequest(url='https://brasilbrokers.com.br/imoveis/load-lista', method='POST', callback=self.parse,  dont_filter= True, formdata=formdata)
            req.meta["formdata"] = formdata
            req.meta["Page"] = str(pagina)
            req.meta['pagina'] = pagina
            yield req

    def parse_detail(self, response):#
        
        if response.url in self.lista_url:
            pass
        else:
            self.lista_url.append(response.url)
            self.qtd_imoveis = len(self.lista_url)

            codigo = response.xpath('//div[@class="agendar-visita"]/div[@class="codigo-imovel"]/text()').re_first(r'(\d+)')
            loader = ItemLoader(items.Property(), response=response)
            # INFORMAÇOES DO IMOVEL (APARENTEMENTE APENAS VENDA NO MOMENTO)
            
            valor_original = response.xpath('//div[@class="aluguel"]/text()').re_first(r'R\$ (.*)')

            iptu = response.xpath('//div[@class="info iptu"]/text()').re_first(r'R\$ (.*)')
            condominio = response.xpath('//div[@class="info condominio"]/text()').re_first(r'R\$ (.*)')
            loader.add_value('valor_iptu', iptu)
            loader.add_value('valor_condominio', condominio)
 
            title = response.xpath('//div[@class="titulo info-imovel"]/h1/text()').getall()
            title = [t.replace('\n','').replace('\r','') for t in title]
            
            if 'à venda' in title:
                negocio = 'Venda'
                loader.add_value('tipo_negocio', negocio)
                loader.add_value('valor', valor_original)
            else:  
                negocio = 'Locação'
                loader.add_value('tipo_negocio', negocio)
                loader.add_value('valor', valor_original)
            

            if len(title) == 2:
                title_address = title[1].split(', ')
                uf = title_address[3].rstrip()
                loader.add_value('uf', uf)
                cidade = title_address[2]
               
                loader.add_value('cidade', cidade)
                loader.add_value('bairro', title_address[1])
                loader.add_value('endereco', title_address[0].lstrip())
                
            else:
                cidade = ''
                loader.add_value('cidade', cidade)
                loader.add_value('bairro', '')
                loader.add_value('endereco', '')
                loader.add_value('uf', '')

            tipo_imovel = response.xpath('//div[@class="titulo info-imovel"]/h1/text()').re_first(r'(.*) à')
            loader.add_value('tipo_imovel', tipo_imovel.lstrip())
            title[0] = title[0].strip()
            title[0] = title[0] if title[0] else '{imovel} para {negocio} em {cidade}/{uf}'.format(imovel=tipo_imovel, negocio=negocio, cidade=title_address[2], uf=uf)
            loader.add_value('title', title[0])

            loader.add_xpath('latitude', '//div[@id="latitude"]/text()')
            loader.add_xpath('longitude', '//div[@id="longitude"]/text()')
            
            area_total = response.xpath('//div[@class="detalhe-imovel area-total"]/div[@class="texto"]/text()').re_first(r'([\d.,]+)m')
            if area_total:
                area = area_total.replace('.','').replace(',','')
                if int(area) >= 5:
                    loader.add_value('area_total', area)
                else: 
                    loader.add_value('area_total', '')
            else:
                loader.add_value('area_total', '')
            
            loader.add_xpath('banheiro', '//div[@class="detalhe-imovel banheiros"]/div[@class="texto"]/text()',re='(\d+) b')
            loader.add_xpath('garagem', '//div[@class="detalhe-imovel vagas "]/div[@class="texto"]/text()',re='(\d+) v') 
            loader.add_xpath('quarto','//div[@class="detalhe-imovel quartos"]/div[@class="texto"]/text()',re='(\d+) d') 
            suite = response.xpath('//div[@class="detalhe-imovel quartos"]//div[@class="small"]/text()').re_first(r'(\d+) s') 
            if suite:
                if int(suite) >= 1:
                    loader.add_value('suite', suite)
                else: 
                    loader.add_value('suite', '')
            else: 
                loader.add_value('suite', '')
            caracteristicas = response.xpath('//div[@class="descricao-imovel"]/div[2]/p/text()').getall()
            caracteristicas = [c and c.replace('\n','').replace('\t','').replace('\r',' ').replace('\xa0','') for c in caracteristicas]
            loader.add_value('caracteristicas', caracteristicas)
            descricao = response.xpath('//div[@class="descricao-imovel"]/div[1]/p/text()').getall()
            descricao = [x and x.replace('\n','').replace('\t','').replace('\r',' ').replace('\xa0','') for x in descricao]
            loader.add_value('descricao', descricao)
            
            loader.add_value('codigo', codigo)  
            loader.add_value('url', response.url)    
            loader.add_value('imobiliaria', 'Brasil Brokers')
            loader.add_value('cidade_imobiliaria', self.cidade_imobiliaria)
            loader.add_value('contato_imobiliaria', self.contato_imobiliaria)
            loader.add_value('uf_imobiliaria', self.uf_imobiliaria)
            loader.add_value('email_imobiliaria', self.email_imobiliaria)
            loader.add_value('endereco_imobiliaria', self.endereco_imobiliaria)
            loader.add_value('bairro_imobiliaria', self.bairro_imobiliaria)
            loader.add_value('creci', self.creci)
            yield loader.load_item()