#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARES API Test - První skript pro stažení dat o firmě
"""

import requests
import json
import xml.etree.ElementTree as ET


def parse_ares_xml(xml_text, ico):
    """
    Parsuje XML odpověď ze starého ARES API
    
    Args:
        xml_text: XML string z ARES
        ico: IČO firmy
    
    Returns:
        dict: Zparsovaná data v jednotné struktuře
    """
    try:
        root = ET.fromstring(xml_text)
        
        # Namespace který ARES používá
        ns = {'are': 'http://wwwinfo.mfcr.cz/ares/xml_doc/schemas/ares/ares_datatypes/v_1.0.3'}
        
        result = {
            'ico': ico,
            'obchodniJmeno': None,
            'pravniForma': None,
            'datumVzniku': None,
            'stavSubjektu': 'AKTIVNÍ',  # Default
            'sidlo': {}
        }
        
        # Hledáme základní údaje
        for zaznam in root.findall('.//are:Zaznam', ns):
            # Obchodní jméno
            obchodni_jmeno = zaznam.find('.//are:Obchodni_firma', ns)
            if obchodni_jmeno is not None:
                result['obchodniJmeno'] = obchodni_jmeno.text
            
            # Datum vzniku
            datum_vzniku = zaznam.find('.//are:Datum_vzniku', ns)
            if datum_vzniku is not None:
                result['datumVzniku'] = datum_vzniku.text
            
            # Adresa
            ulice = zaznam.find('.//are:Nazev_ulice', ns)
            cislo_domovni = zaznam.find('.//are:Cislo_domovni', ns)
            obec = zaznam.find('.//are:Nazev_obce', ns)
            psc = zaznam.find('.//are:PSC', ns)
            
            if ulice is not None:
                result['sidlo']['nazevUlice'] = ulice.text
            if cislo_domovni is not None:
                result['sidlo']['cisloDomovni'] = cislo_domovni.text
            if obec is not None:
                result['sidlo']['nazevObce'] = obec.text
            if psc is not None:
                result['sidlo']['psc'] = psc.text
        
        return result
        
    except Exception as e:
        print(f"Chyba při parsování XML: {e}")
        return None


def get_company_data(ico):
    """
    Stáhne základní data o firmě z ARES API podle IČO
    Zkouší více endpointů jako fallback
    
    Args:
        ico: IČO firmy (string nebo int)
    
    Returns:
        dict: Data o firmě nebo None při chybě
    """
    # Odstranění mezer a konverze na string
    ico = str(ico).strip().replace(" ", "")
    
    # Seznam endpointů k vyzkoušení (fallback mechanismus)
    endpoints = [
        # Nové ARES API (preferované)
        f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}",
        # Alternativní ARES endpoint
        f"https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_std.cgi?ico={ico}",
    ]
    
    print(f"Stahuji data pro IČO: {ico}...")
    
    for idx, url in enumerate(endpoints, 1):
        try:
            print(f"  Zkouším endpoint {idx}/{len(endpoints)}...")
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                # Pokusíme se parsovat jako JSON
                try:
                    data = response.json()
                    print("  ✓ Data úspěšně stažena (JSON)")
                    return data
                except:
                    # Pokud není JSON, může to být XML (starší API)
                    if 'xml' in response.headers.get('content-type', '').lower() or response.text.startswith('<?xml'):
                        print("  ✓ Data stažena (XML) - parsuji...")
                        parsed = parse_ares_xml(response.text, ico)
                        if parsed:
                            return parsed
                        else:
                            continue
                    else:
                        print(f"  ✗ Neočekávaný formát odpovědi")
                        continue
                        
            elif response.status_code == 404:
                print(f"  ✗ Firma nenalezena (404)")
                continue
            else:
                print(f"  ✗ Chyba {response.status_code}")
                continue
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout - API neodpovídá")
            continue
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Chyba připojení: {e}")
            continue
    
    print("\n❌ Nepodařilo se stáhnout data z žádného endpointu.")
    print("Možné příčiny:")
    print("  - IČO neexistuje")
    print("  - ARES API je dočasně nedostupné")
    print("  - Problém s internetovým připojením")
    return None


def parse_company_data(data):
    """
    Zpracuje a vypíše důležitá data o firmě
    
    Args:
        data: Surová data z ARES API
    """
    if not data:
        return
    
    print("\n" + "="*60)
    print("ZÁKLADNÍ INFORMACE O FIRMĚ")
    print("="*60)
    
    # IČO
    ico = data.get('ico')
    print(f"IČO: {ico}")
    
    # Obchodní firma
    obchodni_firma = data.get('obchodniJmeno', 'N/A')
    print(f"Název: {obchodni_firma}")
    
    # Právní forma
    pravni_forma = data.get('pravniForma', 'N/A')
    print(f"Právní forma: {pravni_forma}")
    
    # Datum vzniku
    datum_vzniku = data.get('datumVzniku', 'N/A')
    print(f"Datum vzniku: {datum_vzniku}")
    
    # Stav subjektu
    stavSubjektu = data.get('stavSubjektu', 'N/A')
    print(f"Stav: {stavSubjektu}")
    
    # Adresa sídla
    if 'sidlo' in data:
        sidlo = data['sidlo']
        adresa_parts = []
        
        if 'nazevUlice' in sidlo:
            adresa_parts.append(sidlo['nazevUlice'])
        if 'cisloDomovni' in sidlo:
            adresa_parts.append(str(sidlo['cisloDomovni']))
        if 'nazevObce' in sidlo:
            adresa_parts.append(sidlo['nazevObce'])
        if 'psc' in sidlo:
            adresa_parts.append(str(sidlo['psc']))
            
        adresa = ", ".join(adresa_parts)
        print(f"Sídlo: {adresa}")
    
    # Činnosti (NACE)
    if 'czNace' in data and data['czNace']:
        print(f"\nOdvětví (CZ-NACE):")
        nace_list = data['czNace']
        if isinstance(nace_list, list):
            for nace in nace_list[:3]:  # Zobrazíme max 3 první
                if isinstance(nace, dict):
                    kod = nace.get('kod', 'N/A')
                    nazev = nace.get('nazev', 'N/A')
                    print(f"  - {kod}: {nazev}")
                elif isinstance(nace, str):
                    print(f"  - {nace}")
        elif isinstance(nace_list, str):
            print(f"  - {nace_list}")
    
    print("="*60 + "\n")


def main():
    """
    Hlavní funkce programu
    """
    print("ARES Data Extractor - MVP Test\n")
    
    # Zde zadejte IČO firmy kterou chcete testovat
    # Například: 25596641 (Microsoft s.r.o.)
    test_ico = input("Zadejte IČO firmy: ")
    
    # Stažení dat
    company_data = get_company_data(test_ico)
    
    # Zpracování a výpis
    if company_data:
        parse_company_data(company_data)
        
        # Pro debug - uložení celé JSON odpovědi
        with open('ares_raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(company_data, f, ensure_ascii=False, indent=2)
        print("Kompletní data uložena do souboru: ares_raw_data.json")
    else:
        print("Nepodařilo se stáhnout data.")


if __name__ == "__main__":
    main()
