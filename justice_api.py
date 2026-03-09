#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Justice.cz API - Modul pro stahování a analýzu účetních závěrek
"""

import requests
import json
from datetime import datetime


class JusticeAPI:
    """
    Třída pro práci s účetními závěrkami z Justice.cz
    """
    
    BASE_URL = "https://or.justice.cz/ias/ui/vypis-sl-firma"
    
    def __init__(self, ico):
        """
        Inicializace
        
        Args:
            ico: IČO firmy
        """
        self.ico = str(ico).strip()
        self.financial_statements = []
        
    def fetch_financial_statements(self, years=3):
        """
        Stáhne účetní závěrky z Justice.cz
        
        Args:
            years: Počet let zpětně
            
        Returns:
            list: Seznam účetních závěrek
        """
        print(f"\nStahuji účetní závěrky pro IČO {self.ico}...")
        
        try:
            # Import scraperu
            from justice_scraper import JusticeScraper
            
            scraper = JusticeScraper(self.ico)
            statements = scraper.fetch_all_statements(years)
            
            if statements and len(statements) > 0:
                # Kontrola jestli máme reálná data
                has_real_data = any(
                    stmt['rozvaha']['aktiva_celkem'] is not None 
                    for stmt in statements
                )
                
                if has_real_data:
                    print("  ✓ Reálná data z Justice.cz")
                    return statements
                else:
                    print("  ⚠ Účetní závěrky nalezeny, ale nejsou parsované")
                    print("  ℹ Pro plnou funkci je potřeba zadat data ručně")
                    print("  ℹ Prozatím použijeme vzorová data pro demonstraci")
                    return self._get_mock_data()
            else:
                print("  ⚠ Účetní závěrky nejsou veřejně dostupné")
                print("  ℹ Použijeme vzorová data pro demonstraci funkcionality")
                return self._get_mock_data()
                
        except ImportError:
            print("  ⚠ Scraper není k dispozici")
            print("  ℹ Použijeme vzorová data")
            return self._get_mock_data()
        except Exception as e:
            print(f"  ✗ Chyba při scrapování: {e}")
            print("  ℹ Použijeme vzorová data")
            return self._get_mock_data()
    
    def _get_mock_data(self):
        """
        Mockovaná data pro testování
        Později nahradíme skutečným parserem Justice.cz
        
        Returns:
            list: Vzorové účetní závěrky
        """
        current_year = datetime.now().year
        
        mock_statements = [
            {
                'rok': current_year - 1,
                'rozvaha': {
                    'aktiva_celkem': 50000000,
                    'dlouhodoby_majetek': 20000000,
                    'kratkodoba_aktiva': 28000000,
                    'pohledavky': 15000000,
                    'financni_majetek': 13000000,
                    'pasiva_celkem': 50000000,
                    'vlastni_kapital': 25000000,
                    'cizi_zdroje': 24000000,
                    'bankovni_uvery': 10000000,
                    'kratkodobe_zavazky': 12000000,
                },
                'vysledovka': {
                    'trzby': 80000000,
                    'vynosy_celkem': 82000000,
                    'naklady_celkem': 75000000,
                    'provozni_vysledek': 6500000,
                    'financni_vysledek': -500000,
                    'hospodarsky_vysledek': 5000000,
                    'ebit': 7000000,
                }
            },
            {
                'rok': current_year - 2,
                'rozvaha': {
                    'aktiva_celkem': 45000000,
                    'dlouhodoby_majetek': 18000000,
                    'kratkodoba_aktiva': 26000000,
                    'pohledavky': 14000000,
                    'financni_majetek': 12000000,
                    'pasiva_celkem': 45000000,
                    'vlastni_kapital': 22000000,
                    'cizi_zdroje': 22000000,
                    'bankovni_uvery': 9000000,
                    'kratkodobe_zavazky': 11000000,
                },
                'vysledovka': {
                    'trzby': 70000000,
                    'vynosy_celkem': 72000000,
                    'naklady_celkem': 67000000,
                    'provozni_vysledek': 4500000,
                    'financni_vysledek': -300000,
                    'hospodarsky_vysledek': 4000000,
                    'ebit': 5000000,
                }
            },
            {
                'rok': current_year - 3,
                'rozvaha': {
                    'aktiva_celkem': 40000000,
                    'dlouhodoby_majitel': 16000000,
                    'kratkodoba_aktiva': 23000000,
                    'pohledavky': 12000000,
                    'financni_majetek': 11000000,
                    'pasiva_celkem': 40000000,
                    'vlastni_kapital': 20000000,
                    'cizi_zdroje': 19000000,
                    'bankovni_uvery': 8000000,
                    'kratkodobe_zavazky': 10000000,
                },
                'vysledovka': {
                    'trzby': 60000000,
                    'vynosy_celkem': 62000000,
                    'naklady_celkem': 58000000,
                    'provozni_vysledek': 3500000,
                    'financni_vysledek': -200000,
                    'hospodarsky_vysledek': 3000000,
                    'ebit': 4000000,
                }
            }
        ]
        
        return mock_statements
    
    def calculate_financial_ratios(self, statements):
        """
        Vypočítá finanční ukazatele z účetních závěrek
        
        Args:
            statements: Seznam účetních závěrek
            
        Returns:
            dict: Finanční ukazatele s hodnocením
        """
        if not statements or len(statements) == 0:
            return None
        
        # Bereme nejaktuálnější rok
        latest = statements[0]
        rozvaha = latest['rozvaha']
        vysledovka = latest['vysledovka']
        
        ratios = {}
        
        # 1. ZADLUŽENOST (Debt ratio)
        # Cizí zdroje / Aktiva celkem
        if rozvaha['aktiva_celkem'] > 0:
            debt_ratio = rozvaha['cizi_zdroje'] / rozvaha['aktiva_celkem']
            ratios['zadluzenost'] = {
                'hodnota': debt_ratio,
                'procenta': debt_ratio * 100,
                'hodnoceni': self._evaluate_debt_ratio(debt_ratio),
                'popis': 'Podíl cizích zdrojů na celkových aktivech'
            }
        
        # 2. BĚŽNÁ LIKVIDITA (Current ratio)
        # Oběžná aktiva / Krátkodobé závazky
        if rozvaha['kratkodobe_zavazky'] > 0:
            current_ratio = rozvaha['kratkodoba_aktiva'] / rozvaha['kratkodobe_zavazky']
            ratios['bezna_likvidita'] = {
                'hodnota': current_ratio,
                'hodnoceni': self._evaluate_current_ratio(current_ratio),
                'popis': 'Schopnost splácet krátkodobé závazky'
            }
        
        # 3. RENTABILITA AKTIV (ROA - Return on Assets)
        # Zisk / Aktiva celkem
        if rozvaha['aktiva_celkem'] > 0:
            roa = vysledovka['hospodarsky_vysledek'] / rozvaha['aktiva_celkem']
            ratios['rentabilita_aktiv'] = {
                'hodnota': roa,
                'procenta': roa * 100,
                'hodnoceni': self._evaluate_roa(roa),
                'popis': 'Výnosnost aktiv firmy'
            }
        
        # 4. RENTABILITA VLASTNÍHO KAPITÁLU (ROE)
        # Zisk / Vlastní kapitál
        if rozvaha['vlastni_kapital'] > 0:
            roe = vysledovka['hospodarsky_vysledek'] / rozvaha['vlastni_kapital']
            ratios['rentabilita_kapitalu'] = {
                'hodnota': roe,
                'procenta': roe * 100,
                'hodnoceni': self._evaluate_roe(roe),
                'popis': 'Výnosnost vlastního kapitálu'
            }
        
        # 5. RŮST TRŽEB (pokud máme historii)
        if len(statements) >= 2:
            current_sales = statements[0]['vysledovka']['trzby']
            previous_sales = statements[1]['vysledovka']['trzby']
            
            if previous_sales > 0:
                sales_growth = (current_sales - previous_sales) / previous_sales
                ratios['rust_trzeb'] = {
                    'hodnota': sales_growth,
                    'procenta': sales_growth * 100,
                    'hodnoceni': self._evaluate_sales_growth(sales_growth),
                    'popis': 'Meziroční růst tržeb'
                }
        
        # 6. EBITDA MARGIN
        # (EBIT + odpisy) / Tržby - zjednodušeně použijeme EBIT
        if vysledovka['trzby'] > 0:
            ebit_margin = vysledovka['ebit'] / vysledovka['trzby']
            ratios['ebitda_marze'] = {
                'hodnota': ebit_margin,
                'procenta': ebit_margin * 100,
                'hodnoceni': self._evaluate_ebit_margin(ebit_margin),
                'popis': 'Provozní ziskovost'
            }
        
        return ratios
    
    def _evaluate_debt_ratio(self, ratio):
        """Hodnocení zadluženosti"""
        if ratio < 0.3:
            return {'barva': 'zelena', 'text': 'Nízká zadluženost - konzervativní'}
        elif ratio < 0.6:
            return {'barva': 'zelena', 'text': 'Zdravá zadluženost'}
        elif ratio < 0.8:
            return {'barva': 'oranzova', 'text': 'Zvýšená zadluženost - vyžaduje pozornost'}
        else:
            return {'barva': 'cervena', 'text': 'Vysoká zadluženost - riziko'}
    
    def _evaluate_current_ratio(self, ratio):
        """Hodnocení běžné likvidity"""
        if ratio < 1.0:
            return {'barva': 'cervena', 'text': 'Nedostatečná likvidita - problém'}
        elif ratio < 1.5:
            return {'barva': 'oranzova', 'text': 'Nízká likvidita - opatrnost'}
        elif ratio < 3.0:
            return {'barva': 'zelena', 'text': 'Dobrá likvidita'}
        else:
            return {'barva': 'oranzova', 'text': 'Vysoká likvidita - nevyužitý kapitál'}
    
    def _evaluate_roa(self, roa):
        """Hodnocení rentability aktiv"""
        if roa < 0:
            return {'barva': 'cervena', 'text': 'Ztráta'}
        elif roa < 0.03:
            return {'barva': 'oranzova', 'text': 'Nízká rentabilita'}
        elif roa < 0.10:
            return {'barva': 'zelena', 'text': 'Dobrá rentabilita'}
        else:
            return {'barva': 'zelena', 'text': 'Vysoká rentabilita'}
    
    def _evaluate_roe(self, roe):
        """Hodnocení rentability vlastního kapitálu"""
        if roe < 0:
            return {'barva': 'cervena', 'text': 'Ztráta'}
        elif roe < 0.05:
            return {'barva': 'oranzova', 'text': 'Nízký výnos'}
        elif roe < 0.15:
            return {'barva': 'zelena', 'text': 'Dobrý výnos'}
        else:
            return {'barva': 'zelena', 'text': 'Vysoký výnos'}
    
    def _evaluate_sales_growth(self, growth):
        """Hodnocení růstu tržeb"""
        if growth < -0.05:
            return {'barva': 'cervena', 'text': 'Pokles tržeb'}
        elif growth < 0.05:
            return {'barva': 'oranzova', 'text': 'Stagnace'}
        elif growth < 0.20:
            return {'barva': 'zelena', 'text': 'Zdravý růst'}
        else:
            return {'barva': 'zelena', 'text': 'Silný růst'}
    
    def _evaluate_ebit_margin(self, margin):
        """Hodnocení EBIT marže"""
        if margin < 0:
            return {'barva': 'cervena', 'text': 'Provozní ztráta'}
        elif margin < 0.05:
            return {'barva': 'oranzova', 'text': 'Nízká marže'}
        elif margin < 0.15:
            return {'barva': 'zelena', 'text': 'Dobrá marže'}
        else:
            return {'barva': 'zelena', 'text': 'Vysoká marže'}
    
    def format_ratios_report(self, ratios):
        """
        Naformátuje ukazatele do čitelného reportu
        
        Args:
            ratios: Slovník s finančními ukazateli
            
        Returns:
            str: Formátovaný text
        """
        if not ratios:
            return "Finanční ukazatele nejsou k dispozici"
        
        report = []
        report.append("\n" + "="*60)
        report.append("FINANČNÍ UKAZATELE")
        report.append("="*60)
        
        # Mapping pro hezčí názvy
        names = {
            'zadluzenost': 'Zadluženost',
            'bezna_likvidita': 'Běžná likvidita',
            'rentabilita_aktiv': 'Rentabilita aktiv (ROA)',
            'rentabilita_kapitalu': 'Rentabilita kapitálu (ROE)',
            'rust_trzeb': 'Růst tržeb',
            'ebitda_marze': 'EBITDA marže'
        }
        
        # Symboly pro barvy
        color_symbols = {
            'zelena': '✓',
            'oranzova': '◐',
            'cervena': '✗'
        }
        
        for key, data in ratios.items():
            name = names.get(key, key)
            hodnota = data.get('procenta', data.get('hodnota', 0))
            hodnoceni = data['hodnoceni']
            symbol = color_symbols.get(hodnoceni['barva'], '?')
            
            if 'procenta' in data:
                report.append(f"\n{name}: {hodnota:.1f}% {symbol}")
            else:
                report.append(f"\n{name}: {hodnota:.2f} {symbol}")
            
            report.append(f"  → {hodnoceni['text']}")
            report.append(f"  ({data['popis']})")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)


def test_justice_api():
    """Testovací funkce"""
    print("Test Justice.cz API modulu\n")
    
    ico = "27082440"  # Alza.cz
    
    api = JusticeAPI(ico)
    statements = api.fetch_financial_statements()
    
    if statements:
        print(f"\n✓ Staženo {len(statements)} účetních období")
        
        # Výpočet ukazatelů
        ratios = api.calculate_financial_ratios(statements)
        
        if ratios:
            # Výpis reportu
            report = api.format_ratios_report(ratios)
            print(report)
            
            # Uložení raw dat
            output = {
                'ico': ico,
                'statements': statements,
                'ratios': ratios
            }
            
            with open('financial_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print("\n✓ Data uložena do financial_analysis.json")
    else:
        print("✗ Nepodařilo se stáhnout data")


if __name__ == "__main__":
    test_justice_api()
