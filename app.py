#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trhaktiv Web App - Flask server pro MVP
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import json
from datetime import datetime

# Import našich modulů
from ares_test_v3 import get_company_data
from justice_api import JusticeAPI
from justice_scraper import JusticeScraper

app = Flask(__name__)

# Konfigurace
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'reports'

# Vytvoření složky pro reporty
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """Hlavní stránka"""
    return render_template('index.html')


@app.route('/api/company/<ico>', methods=['GET'])
def get_company_info(ico):
    """
    API endpoint - získání základních dat o firmě
    
    Args:
        ico: IČO firmy
        
    Returns:
        JSON s daty firmy
    """
    try:
        # Stažení dat z ARES
        company_data = get_company_data(ico)
        
        if not company_data:
            return jsonify({
                'success': False,
                'error': 'Firma nebyla nalezena'
            }), 404
        
        # Pokus o nalezení účetních závěrek
        scraper = JusticeScraper(ico)
        statements_urls = scraper.fetch_all_statements(years=3)
        
        # Připravíme odpověď
        response = {
            'success': True,
            'ico': ico,
            'nazev': company_data.get('obchodniJmeno', 'N/A'),
            'pravni_forma': company_data.get('pravniForma', 'N/A'),
            'datum_vzniku': company_data.get('datumVzniku', 'N/A'),
            'sidlo': company_data.get('sidlo', {}),
            'statements_found': statements_urls is not None and len(statements_urls) > 0,
            'statements': []
        }
        
        # Přidáme odkazy na PDF pokud jsou dostupné
        if statements_urls:
            for stmt in statements_urls:
                response['statements'].append({
                    'rok': stmt['rok'],
                    'pdf_url': stmt.get('pdf_url', None)
                })
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_company():
    """
    API endpoint - analýza firmy s finančními daty
    
    Očekává JSON:
    {
        "ico": "12345678",
        "financial_data": {
            "rok": 2023,
            "aktiva_celkem": 50000000,
            "vlastni_kapital": 25000000,
            ...
        }
    }
    
    Returns:
        JSON s kompletní analýzou
    """
    try:
        data = request.get_json()
        
        ico = data.get('ico')
        financial_data = data.get('financial_data')
        
        if not ico or not financial_data:
            return jsonify({
                'success': False,
                'error': 'Chybí povinná data'
            }), 400
        
        # Základní data z ARES
        company_data = get_company_data(ico)
        
        if not company_data:
            return jsonify({
                'success': False,
                'error': 'Firma nebyla nalezena'
            }), 404
        
        # Vytvoření struktury účetní závěrky
        statement = {
            'rok': financial_data.get('rok'),
            'rozvaha': {
                'aktiva_celkem': financial_data.get('aktiva_celkem'),
                'dlouhodoby_majetek': financial_data.get('dlouhodoby_majetek'),
                'kratkodoba_aktiva': financial_data.get('kratkodoba_aktiva'),
                'pohledavky': financial_data.get('pohledavky'),
                'financni_majetek': financial_data.get('financni_majetek'),
                'pasiva_celkem': financial_data.get('pasiva_celkem'),
                'vlastni_kapital': financial_data.get('vlastni_kapital'),
                'cizi_zdroje': financial_data.get('cizi_zdroje'),
                'bankovni_uvery': financial_data.get('bankovni_uvery'),
                'kratkodobe_zavazky': financial_data.get('kratkodobe_zavazky'),
            },
            'vysledovka': {
                'trzby': financial_data.get('trzby'),
                'vynosy_celkem': financial_data.get('vynosy_celkem'),
                'naklady_celkem': financial_data.get('naklady_celkem'),
                'provozni_vysledek': financial_data.get('provozni_vysledek'),
                'financni_vysledek': financial_data.get('financni_vysledek'),
                'hospodarsky_vysledek': financial_data.get('hospodarsky_vysledek'),
                'ebit': financial_data.get('ebit'),
            }
        }
        
        # Výpočet finančních ukazatelů
        justice = JusticeAPI(ico)
        ratios = justice.calculate_financial_ratios([statement])
        
        # Připravíme odpověď
        response = {
            'success': True,
            'ico': ico,
            'nazev': company_data.get('obchodniJmeno', 'N/A'),
            'datum_vzniku': company_data.get('datumVzniku', 'N/A'),
            'ratios': ratios,
            'recommendations': _generate_recommendations(ratios)
        }
        
        # Uložíme report
        report_id = f"{ico}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{report_id}.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        response['report_id'] = report_id
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _generate_recommendations(ratios):
    """
    Generuje doporučení na základě finančních ukazatelů
    
    Args:
        ratios: Finanční ukazatele
        
    Returns:
        list: Seznam doporučení
    """
    recommendations = []
    
    if not ratios:
        return recommendations
    
    # Analýza zadluženosti
    if 'zadluzenost' in ratios:
        debt = ratios['zadluzenost']
        if debt['hodnoceni']['barva'] == 'cervena':
            recommendations.append({
                'priorita': 'vysoká',
                'oblast': 'Zadluženost',
                'text': 'Zvažte refinancování nebo navýšení vlastního kapitálu',
                'nastroje': ['Dluhopis', 'Konvertibilní dluhopis', 'Kapitálový investor']
            })
        elif debt['hodnoceni']['barva'] == 'zelena' and debt['procenta'] < 30:
            recommendations.append({
                'priorita': 'střední',
                'oblast': 'Financování růstu',
                'text': 'Nízká zadluženost otevírá prostor pro výhodné bankovní financování',
                'nastroje': ['Bankovní úvěr', 'Leasing', 'Investiční úvěr']
            })
    
    # Analýza likvidity
    if 'bezna_likvidita' in ratios:
        liquidity = ratios['bezna_likvidita']
        if liquidity['hodnoceni']['barva'] == 'cervena':
            recommendations.append({
                'priorita': 'vysoká',
                'oblast': 'Likvidita',
                'text': 'Zajistěte krátkodobé financování pro pokrytí závazků',
                'nastroje': ['Faktoring', 'Revolvingový úvěr', 'Kontokorent']
            })
    
    # Analýza růstu
    if 'rust_trzeb' in ratios:
        growth = ratios['rust_trzeb']
        if growth['hodnoceni']['barva'] == 'zelena':
            recommendations.append({
                'priorita': 'střední',
                'oblast': 'Růst',
                'text': 'Rostoucí firma je vhodná pro investiční financování',
                'nastroje': ['Venture debt', 'Private equity', 'EU dotace']
            })
    
    # Pokud nejsou specifická doporučení, dáme obecné
    if len(recommendations) == 0:
        recommendations.append({
            'priorita': 'střední',
            'oblast': 'Obecné',
            'text': 'Pro detailní strategii financování doporučujeme individuální konzultaci',
            'nastroje': ['Konzultace', 'Finanční plán']
        })
    
    return recommendations


@app.route('/report/<report_id>')
def view_report(report_id):
    """Zobrazení vygenerovaného reportu"""
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{report_id}.json')
    
    if not os.path.exists(report_path):
        return "Report nenalezen", 404
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    return render_template('report.html', report=report_data)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("TRHAKTIV - FINANČNÍ ANALÝZA MVP")
    print("="*70)
    print("\nServer běží na: http://localhost:5000")
    print("Pro zastavení stiskněte Ctrl+C")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
