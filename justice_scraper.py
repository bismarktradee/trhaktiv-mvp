#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Justice.cz Scraper - Extrakce účetních závěrek ze sbírky listin
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime


class JusticeScraper:
    """
    Scraper pro extrakci účetních závěrek z Justice.cz
    """
    
    BASE_URL = "https://or.justice.cz/ias/ui"
    
    def __init__(self, ico):
        """
        Inicializace scraperu
        
        Args:
            ico: IČO firmy
        """
        self.ico = str(ico).strip()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_company(self):
        """
        Najde firmu v rejstříku podle IČO
        
        Returns:
            str: URL výpisu firmy nebo None
        """
        print(f"Vyhledávám firmu s IČO {self.ico} v rejstříku...")
        
        search_url = f"{self.BASE_URL}/rejstrik-firma.vysledky"
        
        params = {
            'ico': self.ico,
            'jenPlatne': 'PLATNE'
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Hledáme odkaz na detail firmy
                firma_link = soup.find('a', href=re.compile(r'vypis-sl-firma'))
                
                if firma_link:
                    detail_url = firma_link.get('href')
                    if not detail_url.startswith('http'):
                        detail_url = self.BASE_URL + '/' + detail_url.lstrip('/')
                    
                    print(f"  ✓ Firma nalezena: {detail_url}")
                    return detail_url
                else:
                    print("  ✗ Firma nebyla nalezena v rejstříku")
                    return None
            else:
                print(f"  ✗ Chyba při vyhledávání: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ✗ Chyba: {e}")
            return None
    
    def get_sbirka_listin_url(self, company_url):
        """
        Získá URL sbírky listin firmy
        
        Args:
            company_url: URL výpisu firmy
            
        Returns:
            str: URL sbírky listin
        """
        try:
            response = self.session.get(company_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Hledáme odkaz na sbírku listin
                sbirka_link = soup.find('a', href=re.compile(r'vypis-sl-slozka'))
                
                if sbirka_link:
                    sbirka_url = sbirka_link.get('href')
                    if not sbirka_url.startswith('http'):
                        sbirka_url = self.BASE_URL + '/' + sbirka_url.lstrip('/')
                    
                    print(f"  ✓ Sbírka listin nalezena")
                    return sbirka_url
                else:
                    print("  ✗ Sbírka listin nebyla nalezena")
                    return None
            else:
                return None
                
        except Exception as e:
            print(f"  ✗ Chyba: {e}")
            return None
    
    def parse_financial_statements(self, sbirka_url, years=3):
        """
        Parsuje účetní závěrky ze sbírky listin
        
        Args:
            sbirka_url: URL sbírky listin
            years: Počet let zpětně
            
        Returns:
            list: Seznam účetních závěrek
        """
        print(f"Parsuji účetní závěrky...")
        
        try:
            response = self.session.get(sbirka_url, timeout=15)
            
            if response.status_code != 200:
                print(f"  ✗ Chyba při načítání sbírky: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Hledáme dokumenty typu "Účetní závěrka"
            statements = []
            
            # Různé možné texty pro účetní závěrku
            uz_patterns = [
                'účetní závěrka',
                'řádná účetní závěrka',
                'mimořádná účetní závěrka',
                'mezitímní účetní závěrka'
            ]
            
            # Procházíme všechny řádky tabulky
            rows = soup.find_all('tr')
            
            for row in rows:
                text = row.get_text().lower()
                
                # Kontrola jestli obsahuje "účetní závěrka"
                if any(pattern in text for pattern in uz_patterns):
                    
                    # Extrakce roku z textu
                    year_match = re.search(r'20\d{2}', text)
                    if year_match:
                        year = int(year_match.group())
                        
                        # Hledáme odkaz na PDF/dokument
                        pdf_link = row.find('a', href=re.compile(r'\.pdf|dokument'))
                        
                        if pdf_link:
                            doc_url = pdf_link.get('href')
                            if not doc_url.startswith('http'):
                                doc_url = self.BASE_URL + '/' + doc_url.lstrip('/')
                            
                            statements.append({
                                'rok': year,
                                'url': doc_url,
                                'typ': 'účetní závěrka'
                            })
                            
                            print(f"  ✓ Nalezena ÚZ za rok {year}")
            
            # Seřadíme podle roku (nejnovější první)
            statements.sort(key=lambda x: x['rok'], reverse=True)
            
            # Omezíme na požadovaný počet let
            statements = statements[:years]
            
            print(f"  ✓ Celkem nalezeno {len(statements)} účetních závěrek")
            
            return statements
            
        except Exception as e:
            print(f"  ✗ Chyba při parsování: {e}")
            return None
    
    def extract_financial_data_from_pdf(self, pdf_url):
        """
        Extrahuje finanční data z PDF účetní závěrky
        
        POZNÁMKA: Toto je komplexní úloha vyžadující OCR nebo PDF parsing.
        Pro MVP budeme prozatím vracet strukturu kam lze data zadat ručně
        nebo je doplníme později pokročilým parserem.
        
        Args:
            pdf_url: URL PDF dokumentu
            
        Returns:
            dict: Finanční data (prozatím prázdná struktura)
        """
        print(f"    ⚠ PDF parsing není implementován - potřeba ruční zadání")
        
        # Struktura pro finanční data
        financial_data = {
            'rozvaha': {
                'aktiva_celkem': None,
                'dlouhodoby_majetek': None,
                'kratkodoba_aktiva': None,
                'pohledavky': None,
                'financni_majetek': None,
                'pasiva_celkem': None,
                'vlastni_kapital': None,
                'cizi_zdroje': None,
                'bankovni_uvery': None,
                'kratkodobe_zavazky': None,
            },
            'vysledovka': {
                'trzby': None,
                'vynosy_celkem': None,
                'naklady_celkem': None,
                'provozni_vysledek': None,
                'financni_vysledek': None,
                'hospodarsky_vysledek': None,
                'ebit': None,
            },
            'pdf_url': pdf_url,
            'parsed': False
        }
        
        return financial_data
    
    def fetch_all_statements(self, years=3):
        """
        Hlavní metoda - stáhne všechny dostupné účetní závěrky
        
        Args:
            years: Počet let zpětně
            
        Returns:
            list: Seznam účetních závěrek s daty
        """
        # 1. Najdeme firmu
        company_url = self.search_company()
        if not company_url:
            return None
        
        # 2. Získáme sbírku listin
        sbirka_url = self.get_sbirka_listin_url(company_url)
        if not sbirka_url:
            print("  ⚠ Sbírka listin není dostupná")
            return None
        
        # 3. Parsujeme seznam účetních závěrek
        statements_list = self.parse_financial_statements(sbirka_url, years)
        if not statements_list:
            return None
        
        # 4. Pro každou závěrku zkusíme extrahovat data
        complete_statements = []
        
        for statement in statements_list:
            rok = statement['rok']
            pdf_url = statement['url']
            
            print(f"\n  Zpracovávám rok {rok}...")
            
            # Pokus o extrakci dat z PDF
            financial_data = self.extract_financial_data_from_pdf(pdf_url)
            
            complete_statement = {
                'rok': rok,
                'rozvaha': financial_data['rozvaha'],
                'vysledovka': financial_data['vysledovka'],
                'pdf_url': pdf_url,
                'parsed': financial_data['parsed']
            }
            
            complete_statements.append(complete_statement)
        
        return complete_statements


def test_scraper():
    """Testovací funkce"""
    print("="*70)
    print("TEST JUSTICE.CZ SCRAPERU")
    print("="*70 + "\n")
    
    ico = input("Zadejte IČO firmy: ")
    
    scraper = JusticeScraper(ico)
    statements = scraper.fetch_all_statements(years=3)
    
    if statements:
        print("\n" + "="*70)
        print("VÝSLEDEK SCRAPOVÁNÍ")
        print("="*70)
        
        for statement in statements:
            print(f"\nRok: {statement['rok']}")
            print(f"PDF: {statement['pdf_url']}")
            print(f"Parsováno: {'Ano' if statement['parsed'] else 'Ne - vyžaduje ruční zadání'}")
        
        # Uložení do JSON
        output = {
            'ico': ico,
            'statements': statements,
            'scraped_at': datetime.now().isoformat()
        }
        
        filename = f'scraped_statements_{ico}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Data uložena do {filename}")
        
        print("\n" + "="*70)
        print("DALŠÍ KROK")
        print("="*70)
        print("\nPro získání finančních čísel máte dvě možnosti:")
        print("1. Implementovat OCR/PDF parser (složitější)")
        print("2. Umožnit klientovi nahrát čísla ručně (rychlejší pro MVP)")
        
    else:
        print("\n✗ Nepodařilo se získat účetní závěrky")


if __name__ == "__main__":
    test_scraper()
