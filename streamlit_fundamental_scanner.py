import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import warnings
import xml.etree.ElementTree as ET
import urllib.parse
# Suppress warnings
warnings.filterwarnings("ignore")

# Set page config
st.set_page_config(page_title="Ultimate Market Scanner", page_icon="🚀", layout="wide")


# -----------------------------
# ASSET PRESETS
# -----------------------------
PRESETS = {
    "Stocks (Manual)": [], # Handled by text input

    "S&P 500 Leaders": [
        #US100
        "A", "AA", "AACB", "AACBR", "AACBU", "AACG", "AAL", "AAM", "AAME", "AAMI", "AAOI", "AAON", "AAP", "AAPG", "AAPL", "AARD", "AAT", "AAUC", "AB", "ABAT", "ABBV", "ABCB", "ABCL", "ABEO", "ABEV", "ABG", "ABL", "ABLLL", "ABLV", "ABLVW", "ABM", "ABNB", "ABOS", "ABP", "ABPWW", "ABR", "ABR^D", "ABR^E", "ABR^F", "ABSI", "ABT", "ABTC", "ABTS", "ABUS", "ABVC", "ABVE", "ABVEW", "ABVX", "ACA", "ACAD", "ACB", "ACCL", "ACCO", "ACCS", "ACDC", "ACEL", "ACET", "ACFN", "ACGL", "ACGLN", "ACGLO", "ACHC", "ACHR", "ACHV", "ACI", "ACIC", "ACIU", "ACIW", "ACLS", "ACLX", "ACM", "ACMR", "ACN", "ACNB", "ACNT", "ACOG", "ACON", "ACONW", "ACP", "ACP^A", "ACR", "ACR^C", "ACR^D", "ACRE", "ACRS", "ACRV", "ACT", "ACTG", "ACTU", "ACU", "ACV", "ACVA", "ACXP", "AD", "ADAG", "ADAM", "ADAMG", "ADAMH", "ADAMI", "ADAML", "ADAMM", "ADAMN", "ADAMZ", "ADBE", "ADC", "ADC^A", "ADCT", "ADEA", "ADGM", "ADI", "ADIL", "ADM", "ADMA", "ADNT", "ADP", "ADPT", "ADSE", "ADSEW", "ADSK", "ADT", "ADTN", "ADTX", "ADUR", "ADUS", "ADV", "ADVB", "ADVM", "ADX", "ADXN", "AEBI", "AEC", "AEE", "AEF", "AEFC", "AEG", "AEHL", "AEHR", "AEI", "AEIS", "AEM", "AEMD", "AENT", "AENTW", "AEO", "AEON", "AEP", "AER", "AERO", "AERT", "AERTW", "AES", "AESI", "AEVA", "AEVAW", "AEXA", "AEYE", "AFB", "AFBI", "AFCG", "AFG", "AFGB", "AFGC", "AFGD", "AFGE", "AFJK", "AFJKR", "AFJKU", "AFL", "AFRI", "AFRIW", "AFRM", "AFYA", "AG", "AGAE", "AGCC", "AGCO", "AGD", "AGEN", "AGH", "AGI", "AGIO", "AGL", "AGM", "AGM^D", "AGM^E", "AGM^F", "AGM^G", "AGM^H", "AGMH", "AGNC", "AGNCL", "AGNCM", "AGNCN", "AGNCO", "AGNCP", "AGNCZ", "AGO", "AGRO", "AGRZ", "AGX", "AGYS", "AHCO", "AHG", "AHH", "AHH^A", "AHL", "AHL^D", "AHL^E", "AHL^F", "AHMA", "AHR", "AHT", "AHT^D", "AHT^F", "AHT^G", "AHT^H", "AHT^I", "AI", "AIFF", "AIFU", "AIG", "AIHS", "AII", "AIIO", "AIIOW", "AIM", "AIMD", "AIMDW", "AIN", "AIO", "AIOT", "AIP", "AIR", "AIRE", "AIRG", "AIRI", "AIRJ", "AIRJW", "AIRO", "AIRS", "AIRT", "AIRTP", "AISP", "AISPW", "AIT", "AIV", "AIXI", "AIZ", "AIZN", "AJG", "AKA", "AKAM", "AKAN", "AKBA", "AKO/A", "AKO/B", "AKR", "AKRO", "AKTX", "AL", "ALAB", "ALAR", "ALB", "ALB^A", "ALBT", "ALC", "ALCO", "ALCY", "ALDF", "ALDFW", "ALDX", "ALE", "ALEC", "ALEX", "ALF", "ALFUW", "ALG", "ALGM", "ALGN", "ALGS", "ALGT", "ALH", "ALHC", "ALISU", "ALIT", "ALK", "ALKS", "ALKT", "ALL", "ALL^B", "ALL^H", "ALL^I", "ALL^J", "ALLE", "ALLO", "ALLR", "ALLT", "ALLY", "ALM", "ALMS", "ALMU", "ALNT", "ALNY", "ALOT", "ALPS", "ALRM", "ALRS", "ALSN", "ALT", "ALTG", "ALTG^A", "ALTI", "ALTO", "ALTS", "ALUR", "ALV", "ALVO", "ALVOW", "ALX", "ALXO", "ALZN", "AM", "AMAL", "AMAT", "AMBA", "AMBC", "AMBO", "AMBP", "AMBQ", "AMBR", "AMC", "AMCR", "AMCX", "AMD", "AME", "AMG", "AMGN", "AMH", "AMH^G", "AMH^H", "AMIX", "AMKR", "AMLX", "AMN", "AMOD", "AMODW", "AMP", "AMPG", "AMPGW", "AMPH", "AMPL", "AMPX", "AMPY", "AMR", "AMRC", "AMRK", "AMRN", "AMRX", "AMRZ", "AMS", "AMSC", "AMSF", "AMST", "AMT", "AMTB", "AMTD", "AMTM", "AMTX", "AMWD", "AMWL", "AMX", "AMZE", "AMZN", "AN", "ANAB", "ANDE", "ANEB", "ANET", "ANF", "ANG^D", "ANGH", "ANGHW", "ANGI", "ANGO", "ANGX", "ANIK", "ANIP", "ANIX", "ANL", "ANNA", "ANNAW", "ANNX", "ANPA", "ANRO", "ANSC", "ANSCW", "ANTA", "ANTX", "ANVS", "ANY", "AOD", "AOMD", "AOMN", "AOMR", "AON", "AORT", "AOS", "AOSL", "AOUT", "AP", "APA", "APACU", "APAD", "APADR", "APADU", "APAM", "APD", "APEI", "APG", "APGE", "APH", "API", "APLD", "APLE", "APLM", "APLMW", "APLS", "APLT", "APM", "APO", "APO^A", "APOG", "APOS", "APP", "APPF", "APPN", "APPS", "APRE", "APT", "APTV", "APUS", "APVO", "APWC", "APXTU", "APYX", "AQB", "AQMS", "AQN", "AQNB", "AQST", "AR", "ARAI", "ARAY", "ARBB", "ARBE", "ARBEW", "ARBK",
"ARBKL", "ARCB", "ARCC", "ARCO", "ARCT", "ARDC", "ARDT", "ARDX", "ARE", "AREB", "AREBW", "AREC", "AREN", "ARES", "ARES^B", "ARGX", "ARHS", "ARI", "ARKO", "ARKOW", "ARKR", "ARL", "ARLO", "ARLP", "ARM", "ARMK", "ARMN", "ARMP", "AROC", "AROW", "ARQ", "ARQQ", "ARQQW", "ARQT", "ARR", "ARR^C", "ARRY", "ARTL", "ARTNA", "ARTV", "ARTW", "ARVN", "ARW", "ARWR", "ARX", "AS", "ASA", "ASAN", "ASB", "ASB^E", "ASB^F", "ASBA", "ASBP", "ASBPW", "ASC", "ASG", "ASGI", "ASGN", "ASH", "ASIC", "ASIX", "ASLE", "ASM", "ASMB", "ASML", "ASND", "ASNS", "ASO", "ASPC", "ASPCR", "ASPCU", "ASPI", "ASPN", "ASPS", "ASPSW", "ASPSZ", "ASR", "ASRT", "ASRV", "ASST", "ASTC", "ASTE", "ASTH", "ASTI", "ASTL", "ASTLW", "ASTS", "ASUR", "ASX", "ASYS", "ATAI", "ATAT", "ATCH", "ATEC", "ATEN", "ATER", "ATEX", "ATGE", "ATGL", "ATH^A", "ATH^B", "ATH^D", "ATH^E", "ATHA", "ATHE", "ATHM", "ATHR", "ATHS", "ATI", "ATII", "ATIIW", "ATKR", "ATLC", "ATLCL", "ATLCP", "ATLCZ", "ATLN", "ATLO", "ATLX", "ATMC", "ATMCR", "ATMCU", "ATMCW", "ATMU", "ATMV", "ATMVR", "ATMVU", "ATNI", "ATNM", "ATO", "ATOM", "ATON", "ATOS", "ATPC", "ATR", "ATRA", "ATRC", "ATRO", "ATS", "ATUS", "ATXG", "ATXS", "ATYR", "AU", "AUB", "AUB^A", "AUBN", "AUDC", "AUGO", "AUID", "AUNA", "AUPH", "AUR", "AURA", "AURE", "AUROW", "AUST", "AUTL", "AUUD", "AUUDW", "AVA", "AVAH", "AVAL", "AVAV", "AVB", "AVBC", "AVBH", "AVBP", "AVD", "AVDL", "AVGO", "AVIR", "AVK", "AVNS", "AVNT", "AVNW", "AVO", "AVPT", "AVR", "AVT", "AVTR", "AVTX", "AVX", "AVXL", "AVY", "AWF", "AWI", "AWK", "AWP", "AWR", "AWRE", "AWX", "AX", "AXG", "AXGN", "AXIA", "AXIA^", "AXIL", "AXIN", "AXINR", "AXL", "AXON", "AXP", "AXR", "AXS", "AXS^E", "AXSM", "AXTA", "AXTI", "AYI", "AYTU", "AZ", "AZI", "AZN", "AZO", "AZTA", "AZTR", "AZZ", "B", "BA", "BA^A", "BABA", "BAC", "BAC^B", "BAC^E", "BAC^K", "BAC^L", "BAC^M", "BAC^N", "BAC^O", "BAC^P", "BAC^Q", "BAC^S", "BACC", "BACCR", "BACCU", "BACQ", "BACQR", "BAER", "BAERW", "BAFN", "BAH", "BAK", "BALL", "BALY", "BAM", "BANC", "BANC^F", "BAND", "BANF", "BANFP", "BANL", "BANR", "BANX", "BAOS", "BAP", "BARK", "BATL", "BATRA", "BATRK", "BAX", "BB", "BBAI", "BBAR", "BBBY", "BBCP", "BBD", "BBDC", "BBDO", "BBGI", "BBIO", "BBLG", "BBLGW", "BBN", "BBNX", "BBOT", "BBSI", "BBT", "BBU", "BBUC", "BBVA", "BBW", "BBWI", "BBY", "BC", "BC^A", "BC^C", "BCAB", "BCAL", "BCAR", "BCAT", "BCAX", "BCBP", "BCC", "BCDA", "BCE", "BCG", "BCH", "BCIC", "BCML", "BCO", "BCPC", "BCRX", "BCS", "BCSF", "BCTX", "BCTXW", "BCTXZ", "BCV", "BCV^A", "BCX", "BCYC", "BDC", "BDCI", "BDCIU", "BDCIW", "BDJ", "BDL", "BDMD", "BDMDW", "BDN", "BDRX", "BDSX", "BDTX", "BDX", "BE", "BEAG", "BEAGR", "BEAGU", "BEAM", "BEAT", "BEDU", "BEEM", "BEEP", "BEKE", "BELFA", "BELFB", "BEN", "BENF", "BENFW", "BEP", "BEP^A", "BEPC", "BEPH", "BEPI", "BEPJ", "BETA", "BETR", "BETRW", "BF/A", "BF/B", "BFAM", "BFC", "BFH", "BFIN", "BFK", "BFLY", "BFRG", "BFRGW", "BFRI", "BFS", "BFS^D", "BFS^E", "BFST", "BFZ", "BG", "BGB", "BGC", "BGH", "BGI", "BGIN", "BGL", "BGLC", "BGLWW", "BGM", "BGMS", "BGMSP", "BGR", "BGS", "BGSF", "BGSI", "BGT", "BGX", "BGY", "BH", "BHAT", "BHB", "BHC", "BHE", "BHF", "BHFAL", "BHFAM", "BHFAN", "BHFAO", "BHFAP", "BHK", "BHM", "BHP", "BHR", "BHR^B", "BHR^D", "BHRB", "BHST", "BHV", "BHVN", "BIAF", "BIAFW", "BIDU", "BIIB", "BILI", "BILL", "BIO", "BIO/B", "BIOA", "BIOX", "BIP", "BIP^A", "BIP^B", "BIPC", "BIPH", "BIPI", "BIPJ", "BIRD", "BIRK", "BIT", "BITF", "BIVI", "BIYA", "BJ", "BJDX", "BJRI", "BK", "BK^K", "BKD", "BKE", "BKH", "BKHA", "BKHAR", "BKKT", "BKN", "BKNG", "BKR", "BKSY", "BKT", "BKTI", "BKU", "BKV", "BKYI", "BL", "BLBD", "BLBX", "BLCO", "BLD", "BLDP", "BLDR", "BLE", "BLFS", "BLFY", "BLIN",
"BLIV", "BLK", "BLKB", "BLLN", "BLMN", "BLMZ", "BLND", "BLNE", "BLNK", "BLRX", "BLSH", "BLTE", "BLUW", "BLUWU", "BLUWW", "BLW", "BLX", "BLZE", "BLZR", "BLZRU", "BLZRW", "BMA", "BMBL", "BME", "BMEA", "BMEZ", "BMGL", "BMHL", "BMI", "BML^G", "BML^H", "BML^J", "BML^L", "BMN", "BMNR", "BMO", "BMR", "BMRA", "BMRC", "BMRN", "BMY", "BN", "BNAI", "BNAIW", "BNBX", "BNC", "BNCWW", "BNED", "BNGO", "BNH", "BNJ", "BNKK", "BNL", "BNR", "BNRG", "BNS", "BNT", "BNTC", "BNTX", "BNY", "BNZI", "BNZIW", "BOC", "BODI", "BOE", "BOF", "BOH", "BOH^A", "BOH^B", "BOKF", "BOLD", "BOLT", "BON", "BOOM", "BOOT", "BORR", "BOSC", "BOTJ", "BOW", "BOX", "BOXL", "BP", "BPACU", "BPOP", "BPOPM", "BPRN", "BPYPM", "BPYPN", "BPYPO", "BPYPP", "BQ", "BR", "BRAG", "BRBI", "BRBR", "BRBS", "BRC", "BRCB", "BRCC", "BRFH", "BRIA", "BRID", "BRK/A", "BRK/B", "BRKR", "BRKRP", "BRLS", "BRLSW", "BRLT", "BRN", "BRNS", "BRO", "BROS", "BRR", "BRRWW", "BRSL", "BRSP", "BRT", "BRTX", "BRW", "BRX", "BRY", "BRZE", "BSAA", "BSAAU", "BSAC", "BSBK", "BSBR", "BSET", "BSL", "BSLK", "BSLKW", "BSM", "BSRR", "BST", "BSTZ", "BSVN", "BSX", "BSY", "BTA", "BTAI", "BTBD", "BTBDW", "BTBT", "BTCS", "BTCT", "BTDR", "BTE", "BTG", "BTI", "BTM", "BTMD", "BTMWW", "BTO", "BTOC", "BTOG", "BTQ", "BTSG", "BTSGU", "BTT", "BTTC", "BTU", "BTX", "BTZ", "BUD", "BUI", "BULL", "BULLW", "BUR", "BURL", "BURU", "BUSE", "BUSEP", "BUUU", "BV", "BVFL", "BVN", "BVS", "BW", "BW^A", "BWA", "BWAY", "BWB", "BWBBP", "BWEN", "BWFG", "BWG", "BWIN", "BWLP", "BWMN", "BWMX", "BWNB", "BWSN", "BWXT", "BX", "BXC", "BXMT", "BXMX", "BXP", "BXSL", "BY", "BYAH", "BYD", "BYFC", "BYM", "BYND", "BYRN", "BYSI", "BZ", "BZAI", "BZAIW", "BZFD", "BZFDW", "BZH", "BZUN", "C", "C^N", "CAAP", "CAAS", "CABA", "CABO", "CABR", "CAC", "CACC", "CACI", "CADE", "CADE^A", "CADL", "CAE", "CAEP", "CAF", "CAG", "CAH", "CAI", "CAKE", "CAL", "CALC", "CALM", "CALX", "CAMP", "CAMT", "CAN", "CANF", "CANG", "CAPL", "CAPN", "CAPNU", "CAPR", "CAPS", "CAPT", "CAPTW", "CAR", "CARE", "CARG", "CARL", "CARR", "CARS", "CART", "CARV", "CASH", "CASI", "CASS", "CASY", "CAT", "CATO", "CATX", "CATY", "CAVA", "CB", "CBAN", "CBAT", "CBFV", "CBIO", "CBK", "CBL", "CBLL", "CBNA", "CBNK", "CBOE", "CBRE", "CBRL", "CBSH", "CBT", "CBU", "CBUS", "CBZ", "CC", "CCAP", "CCB", "CCBG", "CCC", "CCCC", "CCCX", "CCCXU", "CCCXW", "CCD", "CCEC", "CCEL", "CCEP", "CCG", "CCHH", "CCI", "CCID", "CCIF", "CCII", "CCIIU", "CCIIW", "CCIX", "CCIXW", "CCJ", "CCK", "CCL", "CCLD", "CCLDO", "CCM", "CCNE", "CCNEP", "CCO", "CCOI", "CCRN", "CCS", "CCSI", "CCTG", "CCU", "CCZ", "CD", "CDE", "CDIO", "CDLR", "CDLX", "CDNA", "CDNS", "CDP", "CDR^B", "CDR^C", "CDRE", "CDRO", "CDROW", "CDT", "CDTG", "CDTTW", "CDTX", "CDW", "CDXS", "CDZI", "CDZIP", "CE", "CECO", "CEE", "CEG", "CELC", "CELH", "CELU", "CELUW", "CELZ", "CENN", "CENT", "CENTA", "CENX", "CEP", "CEPF", "CEPO", "CEPT", "CEPU", "CEPV", "CERS", "CERT", "CET", "CETX", "CETY", "CEV", "CEVA", "CF", "CFBK", "CFFI", "CFFN", "CFG", "CFG^E", "CFG^H", "CFG^I", "CFLT", "CFND", "CFR", "CFR^B", "CG", "CGABL", "CGAU", "CGBD", "CGBDL", "CGC", "CGCT", "CGCTW", "CGEM", "CGEN", "CGNT", "CGNX", "CGO", "CGON", "CGTL", "CGTX", "CHA", "CHAC", "CHACR", "CHACU", "CHAR", "CHARR", "CHCI", "CHCO", "CHCT", "CHD", "CHDN", "CHE", "CHEC", "CHECU", "CHECW", "CHEF", "CHEK", "CHGG", "CHH", "CHI", "CHKP", "CHMG", "CHMI", "CHMI^A", "CHMI^B", "CHNR", "CHOW", "CHPG", "CHPGR", "CHPGU", "CHPT", "CHR", "CHRD", "CHRS", "CHRW", "CHSCL", "CHSCM", "CHSCN", "CHSCO", "CHSCP", "CHSN", "CHT", "CHTR", "CHW", "CHWY", "CHY", "CHYM", "CI", "CIA", "CIB", "CICB", "CIEN", "CIF", "CIFR", "CIFRW", "CIG", "CIGI", "CIGL", "CII", "CIIT", "CIK", "CIM",
"CIM^A", "CIM^B", "CIM^C", "CIM^D", "CIMN", "CIMO", "CIMP", "CINF", "CING", "CINGW", "CINT", "CIO", "CIO^A", "CION", "CISO", "CISS", "CIVB", "CIVI", "CIX", "CJET", "CJMB", "CKX", "CL", "CLAR", "CLB", "CLBK", "CLBT", "CLCO", "CLDI", "CLDT", "CLDT^A", "CLDX", "CLF", "CLFD", "CLGN", "CLH", "CLIK", "CLIR", "CLLS", "CLM", "CLMB", "CLMT", "CLNE", "CLNN", "CLNNW", "CLOV", "CLPR", "CLPS", "CLPT", "CLRB", "CLRO", "CLS", "CLSD", "CLSK", "CLSKW", "CLST", "CLVT", "CLW", "CLWT", "CLX", "CLYM", "CM", "CMA", "CMA^B", "CMBM", "CMBT", "CMC", "CMCL", "CMCM", "CMCO", "CMCSA", "CMCT", "CMDB", "CME", "CMG", "CMI", "CMMB", "CMND", "CMP", "CMPO", "CMPOW", "CMPR", "CMPS", "CMPX", "CMRC", "CMRE", "CMRE^B", "CMRE^C", "CMRE^D", "CMS", "CMS^B", "CMS^C", "CMSA", "CMSC", "CMSD", "CMT", "CMTG", "CMTL", "CMU", "CNA", "CNC", "CNCK", "CNCKW", "CNDT", "CNET", "CNEY", "CNF", "CNH", "CNI", "CNK", "CNL", "CNM", "CNMD", "CNNE", "CNO", "CNO^A", "CNOB", "CNOBP", "CNP", "CNQ", "CNR", "CNS", "CNSP", "CNTA", "CNTB", "CNTX", "CNTY", "CNVS", "CNX", "CNXC", "CNXN", "COCH", "COCHW", "COCO", "COCP", "CODA", "CODI", "CODI^A", "CODI^B", "CODI^C", "CODX", "COE", "COEP", "COEPW", "COF", "COF^I", "COF^J", "COF^K", "COF^L", "COF^N", "COFS", "COGT", "COHN", "COHR", "COHU", "COIN", "COKE", "COLA", "COLAR", "COLAU", "COLB", "COLD", "COLL", "COLM", "COMM", "COMP", "CON", "COO", "COOK", "COOT", "COOTW", "COP", "COPL", "COR", "CORT", "CORZ", "CORZW", "CORZZ", "COSM", "COSO", "COST", "COTY", "COUR", "COYA", "CP", "CPA", "CPAC", "CPAY", "CPB", "CPBI", "CPF", "CPHC", "CPHI", "CPIX", "CPK", "CPNG", "CPOP", "CPRI", "CPRT", "CPRX", "CPS", "CPSH", "CPSS", "CPT", "CPZ", "CQP", "CR", "CRACU", "CRAI", "CRAQ", "CRAQR", "CRBD", "CRBG", "CRBP", "CRBU", "CRC", "CRCL", "CRCT", "CRD/A", "CRD/B", "CRDF", "CRDL", "CRDO", "CRE", "CREG", "CRESW", "CRESY", "CREV", "CREVW", "CREX", "CRF", "CRGO", "CRGOW", "CRGY", "CRH", "CRI", "CRIS", "CRK", "CRL", "CRM", "CRMD", "CRML", "CRMLW", "CRMT", "CRNC", "CRNT", "CRNX", "CRON", "CROX", "CRS", "CRSP", "CRSR", "CRT", "CRTO", "CRUS", "CRVL", "CRVO", "CRVS", "CRWD", "CRWS", "CRWV", "CSAI", "CSAN", "CSBR", "CSCO", "CSGP", "CSGS", "CSIQ", "CSL", "CSPI", "CSQ", "CSR", "CSTE", "CSTL", "CSTM", "CSV", "CSW", "CSWC", "CSX", "CTA^A", "CTA^B", "CTAS", "CTBB", "CTBI", "CTDD", "CTEV", "CTGO", "CTKB", "CTLP", "CTM", "CTMX", "CTNM", "CTNT", "CTO", "CTO^A", "CTOR", "CTOS", "CTRA", "CTRE", "CTRI", "CTRM", "CTRN", "CTS", "CTSH", "CTSO", "CTVA", "CTW", "CTXR", "CUB", "CUBB", "CUBE", "CUBI", "CUBI^F", "CUBWU", "CUBWW", "CUE", "CUK", "CULP", "CUPR", "CURB", "CURI", "CURR", "CURV", "CURX", "CUZ", "CV", "CVAC", "CVBF", "CVCO", "CVE", "CVEO", "CVGI", "CVGW", "CVI", "CVKD", "CVLG", "CVLT", "CVM", "CVNA", "CVR", "CVRX", "CVS", "CVU", "CVV", "CVX", "CW", "CWAN", "CWBC", "CWCO", "CWD", "CWEN", "CWH", "CWK", "CWST", "CWT", "CX", "CXAI", "CXAIW", "CXDO", "CXE", "CXH", "CXM", "CXT", "CXW", "CYBN", "CYBR", "CYCN", "CYCU", "CYCUW", "CYD", "CYH", "CYN", "CYPH", "CYRX", "CYTK", "CZFS", "CZNC", "CZR", "CZWI", "D", "DAAQ", "DAAQU", "DAAQW", "DAC", "DAIC", "DAICW", "DAIO", "DAKT", "DAL", "DAN", "DAO", "DAR", "DARE", "DASH", "DAVA", "DAVE", "DAVEW", "DAWN", "DAY", "DB", "DBD", "DBGI", "DBI", "DBL", "DBRG", "DBRG^H", "DBRG^I", "DBRG^J", "DBVT", "DBX", "DC", "DCBO", "DCGO", "DCI", "DCO", "DCOM", "DCOMG", "DCOMP", "DCTH", "DD", "DDC", "DDD", "DDI", "DDL", "DDOG", "DDS", "DDT", "DE", "DEA", "DEC", "DECK", "DEFT", "DEI", "DELL", "DENN", "DEO", "DERM", "DEVS", "DFDV", "DFDVW", "DFH", "DFIN", "DFLI", "DFLIW", "DFP", "DFSC", "DFSCW", "DG", "DGICA", "DGICB", "DGII", "DGLY", "DGNX", "DGX", "DGXX", "DH", "DHC", "DHCNI", "DHCNL", "DHF", "DHI",
"DHIL", "DHR", "DHT", "DHX", "DHY", "DIAX", "DIBS", "DIN", "DINO", "DIOD", "DIS", "DIT", "DJCO", "DJT", "DJTWW", "DK", "DKI", "DKL", "DKNG", "DKS", "DLB", "DLHC", "DLNG", "DLNG^A", "DLO", "DLPN", "DLR", "DLR^J", "DLR^K", "DLR^L", "DLTH", "DLTR", "DLX", "DLXY", "DLY", "DMA", "DMAA", "DMAAR", "DMAAU", "DMAC", "DMB", "DMIIU", "DMLP", "DMO", "DMRC", "DNA", "DNLI", "DNMXU", "DNN", "DNOW", "DNP", "DNTH", "DNUT", "DOC", "DOCN", "DOCS", "DOCU", "DOGZ", "DOLE", "DOMH", "DOMO", "DOOO", "DORM", "DOUG", "DOV", "DOW", "DOX", "DOYU", "DPG", "DPRO", "DPZ", "DQ", "DRCT", "DRD", "DRDB", "DRDBW", "DRH", "DRH^A", "DRI", "DRIO", "DRMA", "DRS", "DRTS", "DRTSW", "DRUG", "DRVN", "DSGN", "DSGR", "DSGX", "DSL", "DSM", "DSP", "DSS", "DSU", "DSWL", "DSX", "DSX^B", "DSY", "DSYWW", "DT", "DTB", "DTCK", "DTE", "DTF", "DTG", "DTI", "DTIL", "DTK", "DTM", "DTSQ", "DTSQR", "DTSQU", "DTSS", "DTST", "DTSTW", "DTW", "DUK", "DUK^A", "DUKB", "DUO", "DUOL", "DUOT", "DV", "DVA", "DVAX", "DVLT", "DVN", "DVS", "DWSN", "DWTX", "DX", "DX^C", "DXC", "DXCM", "DXF", "DXLG", "DXPE", "DXR", "DXST", "DXYZ", "DY", "DYAI", "DYCQ", "DYCQR", "DYN", "DYORU", "E", "EA", "EAD", "EAF", "EAI", "EARN", "EAT", "EB", "EBAY", "EBC", "EBF", "EBMT", "EBON", "EBS", "EC", "ECAT", "ECBK", "ECC           ", "ECC^D", "ECCC", "ECCF", "ECCU", "ECCV", "ECCW", "ECCX", "ECDA", "ECDAW", "ECF", "ECF^A", "ECG", "ECL", "ECO", "ECOR", "ECPG", "ECVT", "ECX", "ECXWW", "ED", "EDAP", "EDBL", "EDBLW", "EDD", "EDF", "EDHL", "EDIT", "EDN", "EDRY", "EDSA", "EDTK", "EDU", "EDUC", "EE", "EEA", "EEFT", "EEIQ", "EEX", "EFC", "EFC^A", "EFC^B", "EFC^C", "EFC^D", "EFOI", "EFR", "EFSC", "EFSCP", "EFSI", "EFT", "EFX", "EFXT", "EG", "EGAN", "EGBN", "EGG", "EGHA", "EGHAR", "EGHT", "EGY", "EH", "EHAB", "EHC", "EHGO", "EHI", "EHLD", "EHTH", "EIC", "EICA", "EICB", "EICC", "EIG", "EIIA", "EIM", "EIX", "EJH", "EKSO", "EL", "ELA", "ELAB", "ELAN", "ELBM", "ELC", "ELDN", "ELF", "ELLO", "ELMD", "ELME", "ELOG", "ELP", "ELPC", "ELPW", "ELS", "ELSE", "ELTK", "ELTX", "ELUT", "ELV", "ELVA", "ELVN", "ELVR", "ELWS", "ELWT", "EM", "EMA", "EMBC", "EMBJ", "EMD", "EME", "EMF", "EMIS", "EMISR", "EML", "EMN", "EMO", "EMP", "EMPD", "EMR", "ENB", "ENGN", "ENGNW", "ENGS", "ENIC", "ENJ", "ENLT", "ENLV", "ENO", "ENOV", "ENPH", "ENR", "ENS", "ENSC", "ENSG", "ENTA", "ENTG", "ENTO", "ENTX", "ENVA", "ENVB", "ENVX", "EOD", "EOG", "EOI", "EOLS", "EONR", "EOS", "EOSE", "EOSEW", "EOT", "EP", "EP^C", "EPAC", "EPAM", "EPC", "EPD", "EPM", "EPOW", "EPR", "EPR^C", "EPR^E", "EPR^G", "EPRT", "EPRX", "EPSM", "EPSN", "EPWK", "EQ", "EQBK", "EQH", "EQH^A", "EQH^C", "EQIX", "EQNR", "EQR", "EQS", "EQT", "EQX", "ERAS", "ERC", "ERH", "ERIC", "ERIE", "ERII", "ERNA", "ERO", "ES", "ESAB", "ESCA", "ESE", "ESEA", "ESGL", "ESHAR", "ESI", "ESLA", "ESLAW", "ESLT", "ESNT", "ESOA", "ESP", "ESPR", "ESQ", "ESRT", "ESS", "ESTA", "ESTC", "ET", "ET^I", "ETB", "ETD", "ETG", "ETHM", "ETHMU", "ETHMW", "ETHZ", "ETI^", "ETJ", "ETN", "ETO", "ETON", "ETOR", "ETR", "ETS", "ETSY", "ETV", "ETW", "ETX           ", "ETY", "EU", "EUDA", "EUDAW", "EURK", "EURKR", "EVAC", "EVAX", "EVC", "EVCM", "EVER", "EVEX", "EVF", "EVG", "EVGN", "EVGO", "EVGOW", "EVH", "EVI", "EVLV", "EVLVW", "EVMN", "EVN", "EVO", "EVOK", "EVOXU", "EVR", "EVRG", "EVT", "EVTC", "EVTL", "EVTV", "EVV", "EW", "EWBC", "EWCZ", "EWTX", "EXAS", "EXC", "EXE", "EXEEL", "EXEL", "EXFY", "EXG", "EXK", "EXLS", "EXOD", "EXOZ", "EXP", "EXPD", "EXPE", "EXPI", "EXPO", "EXR", "EXTR", "EYE", "EYPT", "EZGO", "EZPW", "F", "F^B", "F^C", "F^D", "FA", "FACT", "FACTW", "FAF", "FAMI", "FANG", "FARM", "FAST", "FAT", "FATBB", "FATBP", "FATE", "FATN", "FAX", "FBGL", "FBIN", "FBIO", "FBIOP",
"FBIZ", "FBK", "FBLA", "FBLG", "FBNC", "FBP", "FBRT", "FBRT^E", "FBRX", "FBYD", "FBYDW", "FC", "FCAP", "FCBC", "FCCO", "FCEL", "FCF", "FCFS", "FCHL", "FCN", "FCNCA", "FCNCO", "FCNCP", "FCO", "FCPT", "FCRX", "FCT", "FCUV", "FCX", "FDBC", "FDMT", "FDP", "FDS", "FDSB", "FDUS", "FDX", "FE", "FEAM", "FEBO", "FEDU", "FEIM", "FELE", "FEMY", "FENC", "FENG", "FER", "FERA", "FERAR", "FERG", "FET", "FF", "FFA", "FFAI", "FFAIW", "FFBC", "FFC", "FFIC", "FFIN", "FFIV", "FFWM", "FG", "FGBI", "FGBIP", "FGEN", "FGI", "FGIWW", "FGL", "FGMC", "FGMCR", "FGMCU", "FGN", "FGNX", "FGNXP", "FGSN", "FHB", "FHI", "FHN", "FHN^C", "FHN^E", "FHN^F", "FHTX", "FIBK", "FICO", "FIEE", "FIG", "FIGR", "FIGS", "FIGX", "FIGXU", "FIGXW", "FIHL", "FINS", "FINV", "FINW", "FIP", "FIS", "FISI", "FISV", "FITB", "FITBI", "FITBO", "FITBP", "FIVE", "FIVN", "FIX", "FIZZ", "FKWL", "FLC", "FLD", "FLDDW", "FLEX", "FLG", "FLG^A", "FLG^U", "FLGC", "FLGT", "FLL", "FLNC", "FLNG", "FLNT", "FLO", "FLOC", "FLR", "FLS", "FLUT", "FLUX", "FLWS", "FLX", "FLXS", "FLY", "FLYE", "FLYW", "FLYX", "FMAO", "FMBH", "FMC", "FMFC", "FMN", "FMNB", "FMS", "FMST", "FMSTW", "FMX", "FMY", "FN", "FNB", "FND", "FNF", "FNGR", "FNKO", "FNLC", "FNV", "FNWB", "FNWD", "FOA", "FOF", "FOFO", "FOLD", "FONR", "FOR", "FORA", "FORD", "FORM", "FORR", "FORTY", "FOSL", "FOSLL", "FOUR", "FOUR^A", "FOX", "FOXA", "FOXF", "FOXX", "FOXXW", "FPF", "FPH", "FPI", "FR", "FRA", "FRAF", "FRBA", "FRD", "FRGE", "FRGT", "FRHC", "FRME", "FRMEP", "FRMI", "FRO", "FROG", "FRPH", "FRPT", "FRSH", "FRST", "FRSX", "FRT", "FRT^C", "FSBC", "FSBW", "FSCO", "FSEA", "FSFG", "FSHP", "FSHPR", "FSI", "FSK", "FSLR", "FSLY", "FSM", "FSP", "FSS", "FSSL", "FSTR", "FSUN", "FSV", "FT", "FTAI", "FTAIM", "FTAIN", "FTCI", "FTDR", "FTEK", "FTEL", "FTF", "FTFT", "FTHM", "FTHY", "FTI", "FTK", "FTLF", "FTNT", "FTRE", "FTRK", "FTS", "FTV", "FTW", "FUBO", "FUFU", "FUFUW", "FUL", "FULC", "FULT", "FULTP", "FUN", "FUNC", "FUND", "FURY", "FUSB", "FUSE", "FUSEW", "FUTU", "FVCB", "FVN", "FVNNR", "FVR", "FVRR", "FWONA", "FWONK", "FWRD", "FWRG", "FXNC", "FYBR", "G", "GAB", "GAB^G", "GAB^H", "GAB^K", "GABC", "GAIA", "GAIN", "GAINI", "GAINL", "GAINN", "GAINZ", "GALT", "GAM", "GAM^B", "GAMB", "GAME", "GANX", "GAP", "GASS", "GATX", "GAU", "GAUZ", "GBAB", "GBCI", "GBDC", "GBFH", "GBIO", "GBLI", "GBR", "GBTG", "GBX", "GCBC", "GCI", "GCL", "GCMG", "GCMGW", "GCO", "GCT", "GCTK", "GCTS", "GCV", "GD", "GDC", "GDDY", "GDEN", "GDEV", "GDEVW", "GDHG", "GDL", "GDO", "GDOT", "GDRX", "GDS", "GDTC", "GDV", "GDV^H", "GDV^K", "GDYN", "GE", "GECC", "GECCG", "GECCH", "GECCI", "GECCO", "GEF", "GEG", "GEGGL", "GEHC", "GEL", "GELS", "GEMI", "GEN", "GENC", "GENI", "GENK", "GENVR", "GEO", "GEOS", "GERN", "GES", "GETY", "GEV", "GEVO", "GF", "GFAI", "GFAIW", "GFF", "GFI", "GFL", "GFR", "GFS", "GGAL", "GGB", "GGG", "GGN", "GGN^B", "GGR", "GGROW", "GGT", "GGT^E", "GGT^G", "GGZ", "GH", "GHC", "GHG", "GHI", "GHLD", "GHM", "GHRS", "GHY", "GIB", "GIBO", "GIC", "GIFI", "GIFT", "GIG", "GIGGU", "GIGGW", "GIGM", "GIII", "GIL", "GILD", "GILT", "GIPR", "GIPRW", "GIS", "GITS", "GIW", "GIWWR", "GIWWU", "GJH", "GJO", "GJS", "GJT", "GKOS", "GL", "GL^D", "GLAD", "GLBE", "GLBS", "GLBZ", "GLDD", "GLDG", "GLE", "GLIBA", "GLIBK", "GLMD", "GLNG", "GLO", "GLOB", "GLOP^A", "GLOP^B", "GLOP^C", "GLP", "GLP^B", "GLPG", "GLPI", "GLQ", "GLRE", "GLSI", "GLTO", "GLU", "GLU^B", "GLUE", "GLV", "GLW", "GLXG", "GLXY", "GM", "GMAB", "GME", "GMED", "GMGI", "GMHS", "GMM", "GMRE", "GMRE^A", "GNE", "GNFT", "GNK", "GNL", "GNL^A", "GNL^B", "GNL^D", "GNL^E", "GNLN", "GNLX", "GNPX", "GNRC", "GNS", "GNSS", "GNT", "GNT^A", "GNTA", "GNTX", "GNW", "GO", "GOCO", "GOF", "GOGO",
"GOLF", "GOOD", "GOODN", "GOODO", "GOOG", "GOOGL", "GOOS", "GORO", "GORV", "GOSS", "GOTU", "GOVX", "GP", "GPAT", "GPATW", "GPC", "GPCR", "GPI", "GPJA", "GPK", "GPMT", "GPMT^A", "GPN", "GPOR", "GPRE", "GPRK", "GPRO", "GPUS", "GPUS^D", "GRAB", "GRABW", "GRAF", "GRAL", "GRAN", "GRBK", "GRBK^A", "GRC", "GRCE", "GRDN", "GREE", "GREEL", "GRF", "GRFS", "GRI", "GRMN", "GRND", "GRNQ", "GRNT", "GRO", "GROV", "GROW", "GROY", "GRPN", "GRRR", "GRRRW", "GRVY", "GRWG", "GRX", "GS", "GS^A", "GS^C", "GS^D", "GSAT", "GSBC", "GSBD", "GSHD", "GSHR", "GSHRW", "GSIT", "GSIW", "GSK", "GSL", "GSL^B", "GSM", "GSRF", "GSRFR", "GSRFU", "GSUN", "GT", "GTBP", "GTE", "GTEC", "GTEN", "GTENW", "GTERA", "GTERR", "GTERU", "GTERW", "GTES", "GTIM", "GTLB", "GTLS", "GTLS^B", "GTM", "GTN", "GTX", "GTY", "GUG", "GUT", "GUT^C", "GUTS", "GV", "GVA", "GVH", "GWAV", "GWH", "GWRE", "GWRS", "GWW", "GXAI", "GXO", "GYRE", "GYRO", "H", "HAE", "HAFC", "HAFN", "HAIN", "HAL", "HALO", "HAO", "HAS", "HASI", "HAVAU", "HAYW", "HBAN", "HBANL", "HBANM", "HBANP", "HBB", "HBCP", "HBI", "HBIO", "HBM", "HBNB", "HBNC", "HBR", "HBT", "HCA", "HCAI", "HCAT", "HCC", "HCHL", "HCI", "HCKT", "HCM", "HCMA", "HCMAU", "HCMAW", "HCSG", "HCTI", "HCWB", "HCWC", "HCXY", "HD", "HDB", "HDL", "HDSN", "HE", "HEI", "HEI/A", "HELE", "HEPS", "HEQ", "HERE", "HERZ", "HESM", "HFBL", "HFFG", "HFRO", "HFRO^A", "HFRO^B", "HFWA", "HG", "HGBL", "HGLB", "HGTY", "HGV", "HHH", "HHS", "HI", "HIFS", "HIG", "HIG^G", "HIHO", "HII", "HIMS", "HIMX", "HIND", "HIO", "HIPO", "HIT", "HITI", "HIVE", "HIW", "HIX", "HKD", "HKIT", "HKPD", "HL", "HL^B", "HLF", "HLI", "HLIO", "HLIT", "HLLY", "HLMN", "HLN", "HLNE", "HLP", "HLT", "HLX", "HMC", "HMN", "HMR", "HMY", "HNGE", "HNI", "HNNA", "HNNAZ", "HNRG", "HNST", "HNVR", "HOFT", "HOG", "HOLO", "HOLOW", "HOLX", "HOMB", "HON", "HOOD", "HOPE", "HOTH", "HOUR", "HOUS", "HOV", "HOVNP", "HOVR", "HOVRW", "HOWL", "HP", "HPAI", "HPAIW", "HPE", "HPE^C", "HPF", "HPI", "HPK", "HPP", "HPP^C", "HPQ", "HPS", "HQH", "HQI", "HQL", "HQY", "HR", "HRB", "HRI", "HRL", "HRMY", "HROW", "HRTG", "HRTX", "HRZN", "HSAI", "HSBC", "HSCS", "HSCSW", "HSDT", "HSHP", "HSIC", "HSII", "HSPO", "HSPOU", "HSPOW", "HSPT", "HSPTU", "HST", "HSTM", "HSY", "HTB", "HTBK", "HTCO", "HTCR", "HTD", "HTFB", "HTFC", "HTFL", "HTGC", "HTH", "HTHT", "HTLD", "HTLM", "HTO", "HTOO", "HTOOW", "HTZ", "HTZWW", "HUBB", "HUBC", "HUBCW", "HUBCZ", "HUBG", "HUBS", "HUDI", "HUHU", "HUIZ", "HUM", "HUMA", "HUMAW", "HUN", "HURA", "HURC", "HURN", "HUSA", "HUT", "HUYA", "HVII", "HVIIR", "HVIIU", "HVMC", "HVMCW", "HVT", "HVT/A", "HWBK", "HWC", "HWCPZ", "HWH", "HWKN", "HWM", "HWM^", "HXHX", "HXL", "HY", "HYAC", "HYFM", "HYFT", "HYI", "HYLN", "HYMC", "HYPD", "HYPR", "HYT", "HZO", "IAC", "IAE", "IAF", "IAG", "IART", "IAS", "IAUX", "IBAC", "IBCP", "IBEX", "IBG", "IBIO", "IBKR", "IBM", "IBN", "IBO", "IBOC", "IBP", "IBRX", "IBTA", "ICCC", "ICCM", "ICE", "ICFI", "ICG", "ICHR", "ICL", "ICLR", "ICMB", "ICON", "ICR^A", "ICU", "ICUCW", "ICUI", "IDA", "IDAI", "IDCC", "IDE", "IDN", "IDR", "IDT", "IDXX", "IDYA", "IE", "IEP", "IESC", "IEX", "IFBD", "IFF", "IFN", "IFRX", "IFS", "IGA", "IGC", "IGD", "IGI", "IGIC", "IGR", "IH", "IHD", "IHG", "IHRT", "IHS", "IHT", "IIF", "III", "IIIN", "IIIV", "IIM", "IINN", "IINNW", "IIPR", "IIPR^A", "IKT", "ILAG", "ILLR", "ILLRW", "ILMN", "ILPT", "IMA", "IMAX", "IMCC", "IMCR", "IMDX", "IMG", "IMKTA", "IMMP", "IMMR", "IMMX", "IMNM", "IMNN", "IMO", "IMOS", "IMPP", "IMPPP", "IMRN", "IMRX", "IMSR", "IMSRW", "IMTE", "IMTX", "IMUX", "IMVT", "IMXI", "INAB", "INAC", "INACR", "INACU", "INBK", "INBKZ", "INBS", "INBX", "INCR", "INCY", "INDB", "INDI", "INDO", "INDP", "INDV", "INEO", 
"INFA", "INFU", "INFY", "ING", "INGM", "INGN", "INGR", "INHD", "INKT", "INLF", "INLX", "INM", "INMB", "INMD", "INN", "INN^E", "INN^F", "INNV", "INO", "INOD", "INR", "INSE", "INSG", "INSM", "INSP", "INSW", "INTA", "INTC", "INTG", "INTJ", "INTR", "INTS", "INTT", "INTU", "INTZ", "INUV", "INV", "INVA", "INVE", "INVH", "INVX", "INVZ", "INVZW", "IOBT", "IONQ", "IONR", "IONS", "IOR", "IOSP", "IOT", "IOTR", "IOVA", "IP", "IPAR", "IPCX", "IPCXR", "IPCXU", "IPDN", "IPG", "IPGP", "IPHA", "IPI", "IPM", "IPOD", "IPODW", "IPSC", "IPST", "IPW", "IPWR", "IPX", "IQ", "IQI", "IQST", "IQV", "IR", "IRBT", "IRD", "IRDM", "IREN", "IRIX", "IRM", "IRMD", "IRON", "IROQ", "IRS", "IRT", "IRTC", "IRWD", "ISBA", "ISD", "ISOU", "ISPC", "ISPO", "ISPOW", "ISPR", "ISRG", "ISRL", "ISRLW", "ISSC", "ISTR", "IT", "ITGR", "ITIC", "ITP", "ITRG", "ITRI", "ITRM", "ITRN", "ITT", "ITUB", "ITW", "IVA", "IVDA", "IVDAW", "IVF", "IVP", "IVR", "IVR^C", "IVT", "IVVD", "IVZ", "IX", "IXHL", "IZEA", "IZM", "J", "JACK", "JACS", "JAGX", "JAKK", "JAMF", "JANX", "JAZZ", "JBDI", "JBGS", "JBHT", "JBI", "JBIO", "JBK", "JBL", "JBLU", "JBS", "JBSS", "JBTM", "JCAP", "JCE", "JCI", "JCSE", "JCTC", "JD", "JDZG", "JEF", "JELD", "JEM", "JENA", "JFB", "JFBR", "JFBRW", "JFIN", "JFR", "JFU", "JG", "JGH", "JHG", "JHI", "JHS", "JHX", "JILL", "JJSF", "JKHY", "JKS", "JL", "JLHL", "JLL", "JLS", "JMIA", "JMM", "JMSB", "JNJ", "JOB", "JOBY", "JOE", "JOF", "JOUT", "JOYY", "JPC", "JPM", "JPM^C", "JPM^D", "JPM^J", "JPM^K", "JPM^L", "JPM^M", "JQC", "JRI", "JRS", "JRSH", "JRVR", "JSM", "JSPR", "JSPRW", "JTAI", "JUNS", "JVA", "JWEL", "JXG", "JXN", "JXN^A", "JYD", "JYNT", "JZ", "JZXN", "K", "KAI", "KALA", "KALU", "KALV", "KAPA", "KAR", "KARO", "KAVL", "KB", "KBDC", "KBH", "KBR", "KBSX", "KC", "KCHV", "KCHVR", "KCHVU", "KD", "KDK", "KDKRW", "KDP", "KE", "KELYA", "KELYB", "KEN", "KEP", "KEQU", "KEX", "KEY", "KEY^I", "KEY^J", "KEY^K", "KEY^L", "KEYS", "KF", "KFFB", "KFII", "KFIIR", "KFRC", "KFS", "KFY", "KG", "KGC", "KGEI", "KGS", "KHC", "KIDS", "KIDZ", "KIDZW", "KIM", "KIM^L", "KIM^M", "KIM^N", "KINS", "KIO", "KITT", "KITTW", "KKR", "KKR^D", "KKRS", "KKRT", "KLAC", "KLAR", "KLC", "KLIC", "KLRS", "KLTO", "KLTOW", "KLTR", "KLXE", "KMB", "KMDA", "KMI", "KMPB", "KMPR", "KMRK", "KMT", "KMTS", "KMX", "KN", "KNDI", "KNF", "KNOP", "KNRX", "KNSA", "KNSL", "KNTK", "KNX", "KO", "KOD", "KODK", "KOF", "KOP", "KOPN", "KORE", "KOS", "KOSS", "KOYN", "KOYNU", "KOYNW", "KPLT", "KPLTW", "KPRX", "KPTI", "KR", "KRC", "KREF", "KREF^A", "KRG", "KRKR", "KRMD", "KRMN", "KRNT", "KRNY", "KRO", "KROS", "KRP", "KRRO", "KRT", "KRUS", "KRYS", "KSCP", "KSPI", "KSS", "KT", "KTB", "KTCC", "KTF", "KTH", "KTN", "KTOS", "KTTA", "KTTAW", "KULR", "KURA", "KVAC", "KVACW", "KVHI", "KVUE", "KVYO", "KW", "KWM", "KWMWW", "KWR", "KXIN", "KYIV", "KYIVW", "KYMR", "KYN", "KYTX", "KZIA", "KZR", "L", "LAB", "LAC", "LAD", "LADR", "LAES", "LAFAU", "LAKE", "LAMR", "LAND", "LANDM", "LANDO", "LANDP", "LANV", "LAR", "LARK", "LASE", "LASR", "LATA", "LATAU", "LATAW", "LAUR", "LAW", "LAZ", "LAZR", "LB", "LBGJ", "LBRDA", "LBRDK", "LBRDP", "LBRT", "LBRX", "LBTYA", "LBTYB", "LBTYK", "LC", "LCCC", "LCCCR", "LCFY", "LCFYW", "LCID", "LCII", "LCNB", "LCTX", "LCUT", "LDI", "LDOS", "LDP", "LDWY", "LE", "LEA", "LECO", "LEDS", "LEE", "LEG", "LEGH", "LEGN", "LEGT", "LEN", "LENZ", "LEO", "LESL", "LEU", "LEVI", "LEXX", "LEXXW", "LFCR", "LFMD", "LFMDP", "LFS", "LFST", "LFT", "LFT^A", "LFUS", "LFVN", "LFWD", "LGCB", "LGCL", "LGCY", "LGHL", "LGI", "LGIH", "LGL", "LGN", "LGND", "LGO", "LGPS", "LGVN", "LH", "LHAI", "LHSW", "LHX", "LI", "LICN", "LIDR", "LIDRW", "LIEN", "LIF", "LII", "LILA", "LILAK", "LIMN", "LIN", "LINC",
"LIND", "LINE", "LINK", "LION", "LIQT", "LITB", "LITE", "LITM", "LITS", "LIVE", "LIVN", "LIXT", "LIXTW", "LKFN", "LKQ", "LKSP", "LKSPR", "LKSPU", "LLY", "LLYVA", "LLYVK", "LMAT", "LMB", "LMFA", "LMND", "LMNR", "LMT", "LNAI", "LNC", "LNC^D", "LND", "LNG", "LNKB", "LNKS", "LNN", "LNSR", "LNT", "LNTH", "LNZA", "LNZAW", "LOAN", "LOAR", "LOB", "LOB^A", "LOBO", "LOCL", "LOCO", "LODE", "LOGI", "LOKV", "LOKVU", "LOKVW", "LOMA", "LOOP", "LOPE", "LOT", "LOTWW", "LOVE", "LOW", "LPA", "LPAA", "LPAAW", "LPBB", "LPBBW", "LPCN", "LPG", "LPL", "LPLA", "LPRO", "LPSN", "LPTH", "LPX", "LQDA", "LQDT", "LRCX", "LRE", "LRHC", "LRMR", "LRN", "LSAK", "LSBK", "LSCC", "LSE", "LSF", "LSH", "LSPD", "LSTA", "LSTR", "LTBR", "LTC", "LTCC", "LTH", "LTM", "LTRN", "LTRX", "LTRYW", "LU", "LUCD", "LUCK", "LUCY", "LUCYW", "LUD", "LULU", "LUMN", "LUNG", "LUNR", "LUV", "LUXE", "LVLU", "LVO", "LVRO", "LVROW", "LVS", "LVTX", "LVWR", "LW", "LWAC", "LWACU", "LWACW", "LWAY", "LWLG", "LX", "LXEH", "LXEO", "LXFR", "LXP", "LXP^C", "LXRX", "LXU", "LYB", "LYEL", "LYFT", "LYG", "LYRA", "LYTS", "LYV", "LZ", "LZB", "LZM", "LZMH", "M", "MA", "MAA", "MAA^I", "MAAS", "MAC", "MACI", "MACIW", "MAGH", "MAGN", "MAIA", "MAIN", "MAMA", "MAMK", "MAMO", "MAN", "MANH", "MANU", "MAPS", "MAPSW", "MAR", "MARA", "MARPS", "MAS", "MASI", "MASK", "MASS", "MAT", "MATH", "MATV", "MATW", "MATX", "MAX", "MAXN", "MAYA", "MAYAR", "MAYS", "MAZE", "MB", "MBAV", "MBAVW", "MBBC", "MBC", "MBCN", "MBI", "MBIN", "MBINL", "MBINM", "MBINN", "MBIO", "MBLY", "MBNKO", "MBOT", "MBRX", "MBUU", "MBVI", "MBVIU", "MBVIW", "MBWM", "MBX", "MC", "MCB", "MCBS", "MCD", "MCFT", "MCGA", "MCGAU", "MCGAW", "MCHB", "MCHP", "MCHPP", "MCHX", "MCI", "MCK", "MCN", "MCO", "MCR", "MCRB", "MCRI", "MCRP", "MCS", "MCTR", "MCW", "MCY", "MD", "MDAI", "MDAIW", "MDB", "MDBH", "MDCX", "MDCXW", "MDGL", "MDIA", "MDLZ", "MDRR", "MDT", "MDU", "MDV", "MDV^A", "MDWD", "MDXG", "MDXH", "MEC", "MED", "MEDP", "MEG", "MEGI", "MEGL", "MEHA", "MEI", "MELI", "MENS", "MEOH", "MER^K", "MERC", "MESA", "MESO", "MET", "MET^A", "MET^E", "MET^F", "META", "METC", "METCB", "METCI", "METCZ", "MFA", "MFA^B", "MFA^C", "MFAN", "MFAO", "MFC", "MFG", "MFI", "MFIC", "MFICL", "MFIN", "MFM", "MG", "MGA", "MGEE", "MGF", "MGIC", "MGIH", "MGLD", "MGM", "MGN", "MGNI", "MGNX", "MGPI", "MGR", "MGRB", "MGRC", "MGRD", "MGRE", "MGRT", "MGRX", "MGTX", "MGX", "MGY", "MGYR", "MH", "MHD", "MHF", "MHH", "MHK", "MHLA", "MHN", "MHNC", "MHO", "MHUA", "MI", "MIAX", "MIDD", "MIGI", "MIMI", "MIN", "MIND", "MIR", "MIRA", "MIRM", "MIST", "MITK", "MITN", "MITP", "MITQ", "MITT", "MITT^A", "MITT^B", "MITT^C", "MIY", "MKC", "MKDW", "MKDWW", "MKL", "MKLY", "MKLYR", "MKLYU", "MKSI", "MKTW", "MKTX", "MKZR", "MLAB", "MLAC", "MLACR", "MLCI", "MLCO", "MLEC", "MLECW", "MLGO", "MLI", "MLKN", "MLM", "MLP", "MLR", "MLSS", "MLTX", "MLYS", "MMA", "MMC", "MMD", "MMI", "MMLP", "MMM", "MMS", "MMSI", "MMT", "MMTXU", "MMU", "MMYT", "MNDO", "MNDR", "MNDY", "MNKD", "MNMD", "MNOV", "MNPR", "MNR", "MNRO", "MNSB", "MNSBP", "MNSO", "MNST", "MNTK", "MNTN", "MNTS", "MNTSW", "MNY", "MNYWW", "MO", "MOB", "MOBBW", "MOBX", "MOD", "MODD", "MODG", "MOFG", "MOGO", "MOGU", "MOH", "MOLN", "MOMO", "MORN", "MOS", "MOV", "MOVE", "MP", "MPA", "MPAA", "MPB", "MPC", "MPLT", "MPLX", "MPTI", "MPU", "MPV", "MPW", "MPWR", "MPX", "MQ", "MQT", "MQY", "MRAM", "MRBK", "MRCC", "MRCY", "MREO", "MRK", "MRKR", "MRM", "MRNA", "MRNO", "MRNOW", "MRP", "MRSN", "MRT", "MRTN", "MRUS", "MRVI", "MRVL", "MRX", "MS", "MS^A", "MS^E", "MS^F", "MS^I", "MS^K", "MS^L", "MS^O", "MS^P", "MS^Q", "MSA", "MSAI", "MSAIW", "MSB", "MSBI", "MSBIP", "MSC", "MSCI", "MSD", "MSDL", "MSEX", "MSFT", "MSGE", "MSGM", 
"MSGS", "MSGY", "MSI", "MSIF", "MSM", "MSN", "MSPR", "MSPRW", "MSPRZ", "MSS", "MSTR", "MSW", "MT", "MTA", "MTB", "MTB^H", "MTB^J", "MTB^K", "MTC", "MTCH", "MTD", "MTDR", "MTEK", "MTEKW", "MTEN", "MTEX", "MTG", "MTH", "MTLS", "MTN", "MTNB", "MTR", "MTRN", "MTRX", "MTSI", "MTSR", "MTUS", "MTVA", "MTW", "MTX", "MTZ", "MU", "MUA", "MUC", "MUE", "MUFG", "MUJ", "MUR", "MURA", "MUSA", "MUX", "MVBF", "MVF", "MVIS", "MVO", "MVST", "MVSTW", "MVT", "MWA", "MWG", "MWYN", "MX", "MXC", "MXCT", "MXE", "MXF", "MXL", "MYD", "MYE", "MYFW", "MYGN", "MYI", "MYN", "MYND", "MYNZ", "MYO", "MYPS", "MYPSW", "MYRG", "MYSE", "MYSEW", "MYSZ", "MZTI", "NA", "NAAS", "NABL", "NAC", "NAD", "NAGE", "NAII", "NAK", "NAKA", "NAMI", "NAMM", "NAMMW", "NAMS", "NAMSW", "NAN", "NAOV", "NAT", "NATH", "NATL", "NATR", "NAUT", "NAVI", "NAVN", "NAZ", "NB", "NBB", "NBBK", "NBH", "NBHC", "NBIS", "NBIX", "NBN", "NBP", "NBR", "NBTB", "NBTX", "NBXG", "NBY", "NC", "NCA", "NCDL", "NCEL", "NCEW", "NCI", "NCL", "NCLH", "NCMI", "NCNA", "NCNO", "NCPL", "NCRA", "NCSM", "NCT", "NCTY", "NCV", "NCV^A", "NCZ", "NCZ^A", "NDAQ", "NDLS", "NDMO", "NDRA", "NDSN", "NE", "NEA", "NECB", "NEE", "NEE^N", "NEE^S", "NEE^T", "NEE^U", "NEGG", "NEM", "NEN", "NEO", "NEOG", "NEON", "NEOV", "NEOVW", "NEPH", "NERV", "NESR", "NET", "NETD", "NETDW", "NEU", "NEUP", "NEWP", "NEWT", "NEWTG", "NEWTH", "NEWTI", "NEWTP", "NEWTZ", "NEXA", "NEXM", "NEXN", "NEXT", "NFBK", "NFE", "NFG", "NFGC", "NFJ", "NFLX", "NG", "NGD", "NGG", "NGL", "NGL^B", "NGL^C", "NGNE", "NGS", "NGVC", "NGVT", "NHC", "NHI", "NHICW", "NHPAP", "NHPBP", "NHS", "NHTC", "NI", "NIC", "NICE", "NIE", "NIM", "NINE", "NIO", "NIOBW", "NIPG", "NIQ", "NISN", "NITO", "NIU", "NIVF", "NIVFW", "NIXX", "NIXXW", "NJR", "NKE", "NKLR", "NKSH", "NKTR", "NKTX", "NKX", "NL", "NLOP", "NLY", "NLY^F", "NLY^G", "NLY^I", "NLY^J", "NMAI", "NMAX", "NMCO", "NMFC", "NMFCZ", "NMG", "NMI", "NMIH", "NML", "NMM", "NMP", "NMPAU", "NMR", "NMRA", "NMRK", "NMS", "NMT", "NMTC", "NMZ", "NN", "NNAVW", "NNBR", "NNDM", "NNE", "NNI", "NNN", "NNNN", "NNOX", "NNVC", "NNY", "NOA", "NOAH", "NOC", "NODK", "NOEM", "NOEMR", "NOEMW", "NOG", "NOK", "NOM", "NOMA", "NOMD", "NOTE", "NOTV", "NOV", "NOVT", "NOVTU", "NOW", "NP", "NPAC", "NPACU", "NPACW", "NPB", "NPCE", "NPCT", "NPFD", "NPK", "NPKI", "NPO", "NPT", "NPV", "NPWR", "NQP", "NRC", "NRDS", "NRDY", "NREF", "NREF^A", "NRG", "NRGV", "NRIM", "NRIX", "NRK", "NRO", "NRP", "NRSN", "NRSNW", "NRT", "NRUC", "NRXP", "NRXPW", "NRXS", "NSA", "NSA^A", "NSC", "NSIT", "NSP", "NSPR", "NSRX", "NSSC", "NSTS", "NSYS", "NTAP", "NTB", "NTCL", "NTCT", "NTES", "NTGR", "NTHI", "NTIC", "NTIP", "NTLA", "NTNX", "NTR", "NTRA", "NTRB", "NTRBW", "NTRP", "NTRS", "NTRSO", "NTSK", "NTST", "NTWK", "NTWO", "NTWOW", "NTZ", "NU", "NUAI", "NUAIW", "NUE", "NUKK", "NUKKW", "NUS", "NUTX", "NUV", "NUVB", "NUVL", "NUW", "NUWE", "NVA", "NVAWW", "NVAX", "NVCR", "NVCT", "NVDA", "NVEC", "NVG", "NVGS", "NVMI", "NVNI", "NVNIW", "NVNO", "NVO", "NVR", "NVRI", "NVS", "NVST", "NVT", "NVTS", "NVVE", "NVVEW", "NVX", "NWBI", "NWE", "NWFL", "NWG", "NWGL", "NWL", "NWN", "NWPX", "NWS", "NWSA", "NWTG", "NX", "NXC", "NXDR", "NXDT", "NXDT^A", "NXE", "NXG", "NXGL", "NXGLW", "NXJ", "NXL", "NXN", "NXP", "NXPI", "NXPL", "NXRT", "NXST", "NXT", "NXTC", "NXTT", "NXXT", "NYAX", "NYC", "NYT", "NYXH", "NZF", "O", "OABI", "OABIW", "OACC", "OACCW", "OAK^A", "OAK^B", "OAKU", "OBA", "OBAWW", "OBDC", "OBE", "OBIO", "OBK", "OBLG", "OBT", "OC", "OCC", "OCCI", "OCCIM", "OCCIN", "OCCIO", "OCFC", "OCG", "OCGN", "OCS", "OCSAW", "OCSL", "OCUL", "ODC", "ODD", "ODFL", "ODP", "ODV", "ODVWZ", "ODYS", "OEC", "OESX", "OFAL", "OFG", "OFIX", "OFLX", "OFS", "OFSSH", "OGE",
"OGEN", "OGI", "OGN", "OGS", "OHI", "OI", "OIA", "OII", "OIS", "OKE", "OKLO", "OKTA", "OKUR", "OKYO", "OLB", "OLED", "OLLI", "OLMA", "OLN", "OLP", "OLPX", "OM", "OMAB", "OMC", "OMCC", "OMCL", "OMDA", "OMER", "OMEX", "OMF", "OMH", "OMI", "OMSE", "ON", "ONB", "ONBPO", "ONBPP", "ONC", "ONCH", "ONCHU", "ONCHW", "ONCO", "ONCY", "ONDS", "ONEG", "ONEW", "ONFO", "ONIT", "ONL", "ONMD", "ONMDW", "ONON", "ONTF", "ONTO", "OOMA", "OP", "OPAD", "OPAL", "OPBK", "OPCH", "OPEN", "OPFI", "OPHC", "OPK", "OPP", "OPP^A", "OPP^B", "OPP^C", "OPRA", "OPRT", "OPRX", "OPTT", "OPTX", "OPTXW", "OPXS", "OPY", "OR", "ORA", "ORBS", "ORC", "ORCL", "ORGN", "ORGNW", "ORGO", "ORI", "ORIC", "ORIQ", "ORIQU", "ORIQW", "ORIS", "ORKA", "ORKT", "ORLA", "ORLY", "ORMP", "ORN", "ORRF", "OS", "OSBC", "OSCR", "OSIS", "OSK", "OSPN", "OSRH", "OSRHW", "OSS", "OSTX", "OSUR", "OSW", "OTEX", "OTF", "OTGA", "OTGAU", "OTGAW", "OTIS", "OTLK", "OTLY", "OTTR", "OUST", "OUSTZ", "OUT", "OVBC", "OVID", "OVLY", "OVV", "OWL", "OWLS", "OWLT", "OXBR", "OXBRW", "OXLC", "OXLCG", "OXLCI", "OXLCL", "OXLCN", "OXLCO", "OXLCP", "OXLCZ", "OXM", "OXSQ", "OXSQG", "OXSQH", "OXY", "OYSE", "OYSER", "OYSEU", "OZ", "OZK", "OZKAP", "PAA", "PAAS", "PAC", "PACB", "PACH", "PACHU", "PACHW", "PACK", "PACS", "PAG", "PAGP", "PAGS", "PAHC", "PAI", "PAII", "PAL", "PALI", "PAM", "PAMT", "PANL", "PANW", "PAPL", "PAR", "PARR", "PASG", "PASW", "PATH", "PATK", "PAVM", "PAVS", "PAX", "PAXS", "PAY", "PAYC", "PAYO", "PAYS", "PAYX", "PB", "PBA", "PBBK", "PBF", "PBFS", "PBH", "PBHC", "PBI", "PBI^B", "PBM", "PBMWW", "PBR", "PBT", "PBYI", "PCAP", "PCAPU", "PCAR", "PCB", "PCF", "PCG", "PCG^A", "PCG^B", "PCG^C", "PCG^D", "PCG^E", "PCG^G", "PCG^H", "PCG^I", "PCG^X", "PCH", "PCLA", "PCM", "PCN", "PCOR", "PCQ", "PCRX", "PCSA", "PCSC", "PCT", "PCTTU", "PCTTW", "PCTY", "PCVX", "PCYO", "PD", "PDCC", "PDD", "PDEX", "PDFS", "PDI", "PDLB", "PDM", "PDO", "PDPA", "PDS", "PDSB", "PDT", "PDX", "PDYN", "PDYNW", "PEB", "PEB^E", "PEB^F", "PEB^G", "PEB^H", "PEBK", "PEBO", "PECO", "PED", "PEG", "PEGA", "PELI", "PELIR", "PELIU", "PEN", "PENG", "PENN", "PEO", "PEP", "PEPG", "PERF", "PERI", "PESI", "PETS", "PETZ", "PEW", "PFAI", "PFBC", "PFD", "PFE", "PFG", "PFGC", "PFH", "PFIS", "PFL", "PFLT", "PFN", "PFO", "PFS", "PFSA", "PFSI", "PFX", "PFXNZ", "PG", "PGAC", "PGACR", "PGC", "PGEN", "PGNY", "PGP", "PGR", "PGRE", "PGY", "PGYWW", "PGZ", "PH", "PHAR", "PHAT", "PHG", "PHGE", "PHI", "PHIN", "PHIO", "PHK", "PHM", "PHOE", "PHR", "PHUN", "PHVS", "PHXE^", "PI", "PII", "PIII", "PIIIW", "PIM", "PINC", "PINE", "PINS", "PIPR", "PJT", "PK", "PKBK", "PKE", "PKG", "PKOH", "PKST", "PKX", "PL", "PLAB", "PLAG", "PLAY", "PLBC", "PLBL", "PLBY", "PLCE", "PLD", "PLG", "PLMK", "PLMKW", "PLMR", "PLNT", "PLOW", "PLPC", "PLRX", "PLRZ", "PLSE", "PLTK", "PLTR", "PLUG", "PLUR", "PLUS", "PLUT", "PLX", "PLXS", "PLYM", "PM", "PMAX", "PMCB", "PMEC", "PMI", "PML", "PMM", "PMN", "PMNT", "PMO", "PMT", "PMT^A", "PMT^B", "PMT^C", "PMTR", "PMTRU", "PMTRW", "PMTS", "PMTU", "PMTV", "PMTW", "PMVP", "PN", "PNBK", "PNC", "PNFP", "PNFPP", "PNI", "PNNT", "PNR", "PNRG", "PNTG", "PNW", "POAI", "POAS", "POCI", "PODC", "PODD", "POET", "POLA", "POLE", "POLEU", "POLEW", "POM", "PONY", "POOL", "POR", "POST", "POWI", "POWL", "POWW", "POWWP", "PPBT", "PPC", "PPCB", "PPG", "PPIH", "PPL", "PPSI", "PPT", "PPTA", "PR", "PRA", "PRAA", "PRAX", "PRCH", "PRCT", "PRDO", "PRE", "PRENW", "PRFX", "PRG", "PRGO", "PRGS", "PRH", "PRHI", "PRHIZ", "PRI", "PRIF^D", "PRIF^J", "PRIF^K", "PRIF^L", "PRIM", "PRK", "PRKS", "PRLB", "PRLD", "PRM", "PRMB", "PRME", "PRO", "PROF", "PROK", "PROP", "PROV", "PRPH", "PRPL", "PRPO", "PRQR", "PRS", "PRSO", "PRSU", "PRT", 
"PRTA", "PRTC", "PRTH", "PRTS", "PRU", "PRVA", "PRZO", "PSA", "PSA^F", "PSA^G", "PSA^H", "PSA^I", "PSA^J", "PSA^K", "PSA^L", "PSA^M", "PSA^N", "PSA^O", "PSA^P", "PSA^Q", "PSA^R", "PSA^S", "PSBD", "PSEC", "PSEC^A", "PSF", "PSFE", "PSHG", "PSIG", "PSIX", "PSKY", "PSMT", "PSN", "PSNL", "PSNY", "PSNYW", "PSO", "PSQH", "PSTG", "PSTL", "PSTV", "PSX", "PT", "PTA", "PTC", "PTCT", "PTEN", "PTGX", "PTHL", "PTHS", "PTIX", "PTIXW", "PTLE", "PTLO", "PTN", "PTON", "PTRN", "PTY", "PUBM", "PUK", "PULM", "PUMP", "PVBC", "PVH", "PVL", "PVLA", "PW", "PW^A", "PWP", "PWR", "PX", "PXED", "PXLW", "PXS", "PYPD", "PYPL", "PYT", "PYXS", "PZG", "PZZA", "Q", "QBTS", "QCLS", "QCOM", "QCRH", "QD", "QDEL", "QETA", "QETAR", "QFIN", "QGEN", "QH", "QIPT", "QLGN", "QLYS", "QMCO", "QNCX", "QNRX", "QNST", "QNTM", "QQQX", "QRHC", "QRVO", "QS", "QSEA", "QSI", "QSIAW", "QSR", "QTRX", "QTTB", "QTWO", "QUAD", "QUBT", "QUIK", "QUMS", "QUMSR", "QUMSU", "QURE", "QVCC", "QVCD", "QVCGA", "QVCGP", "QXO", "QXO^B", "R", "RA", "RAAQ", "RAAQU", "RAAQW", "RAC", "RAC/WS", "RACE", "RADX", "RAIL", "RAIN", "RAINW", "RAL", "RAMP", "RAND", "RANG", "RANGR", "RANI", "RAPP", "RAPT", "RARE", "RAVE", "RAY", "RAYA", "RBA", "RBB", "RBBN", "RBC", "RBCAA", "RBKB", "RBLX", "RBNE", "RBOT", "RBRK", "RC", "RC^C", "RC^E", "RCAT", "RCB", "RCC", "RCD", "RCEL", "RCG", "RCI", "RCKT", "RCKY", "RCL", "RCMT", "RCON", "RCS", "RCT", "RCUS", "RDAC", "RDACR", "RDACU", "RDAG", "RDAGU", "RDAGW", "RDCM", "RDDT", "RDGT", "RDHL", "RDI", "RDIB", "RDN", "RDNT", "RDNW", "RDVT", "RDW", "RDWR", "RDY", "RDZN", "RDZNW", "REAL", "REAX", "REBN", "RECT", "REE", "REFI", "REFR", "REG", "REGCO", "REGCP", "REGN", "REI", "REKR", "RELI", "RELIW", "RELL", "RELX", "RELY", "RENT", "REPL", "REPX", "RERE", "RES", "RETO", "REVB", "REVBW", "REVG", "REX", "REXR", "REXR^B", "REXR^C", "REYN", "REZI", "RF", "RF^C", "RF^E", "RF^F", "RFAI", "RFAIR", "RFI", "RFIL", "RFL", "RFM", "RFMZ", "RGA", "RGC", "RGCO", "RGEN", "RGLD", "RGNX", "RGP", "RGR", "RGS", "RGT", "RGTI", "RGTIW", "RH", "RHI", "RHLD", "RHP", "RIBB", "RIBBU", "RICK", "RIG", "RIGL", "RILY", "RILYG", "RILYK", "RILYL", "RILYN", "RILYP", "RILYT", "RILYZ", "RIME", "RIO", "RIOT", "RITM", "RITM^A", "RITM^B", "RITM^C", "RITM^D", "RITM^E", "RITR", "RIV", "RIV^A", "RIVN", "RJF", "RJF^B", "RKDA", "RKLB", "RKT", "RL", "RLAY", "RLGT", "RLI", "RLJ", "RLJ^A", "RLMD", "RLTY", "RLX", "RLYB", "RM", "RMAX", "RMBI", "RMBS", "RMCF", "RMCO", "RMCOW", "RMD", "RMI", "RMM", "RMMZ", "RMNI", "RMR", "RMSG", "RMSGW", "RMT", "RMTI", "RNA", "RNAC", "RNAZ", "RNG", "RNGR", "RNGTU", "RNP", "RNR", "RNR^F", "RNR^G", "RNST", "RNTX", "RNW", "RNWWW", "RNXT", "ROAD", "ROCK", "ROG", "ROIV", "ROK", "ROKU", "ROL", "ROLR", "ROMA", "ROOT", "ROP", "ROST", "RPAY", "RPD", "RPGL", "RPID", "RPM", "RPRX", "RPT", "RPT^C", "RPTX", "RQI", "RR", "RRBI", "RRC", "RRGB", "RRR", "RRX", "RS", "RSF", "RSG", "RSI", "RSKD", "RSSS", "RSVR", "RSVRW", "RTAC", "RTACU", "RTACW", "RTO", "RTX", "RUBI", "RUM", "RUMBW", "RUN", "RUSHA", "RUSHB", "RVLV", "RVMD", "RVMDW", "RVP", "RVPH", "RVPHW", "RVSB", "RVSN", "RVSNW", "RVT", "RVTY", "RVYL", "RWAY", "RWAYL", "RWAYZ", "RWT", "RWT^A", "RWTN", "RWTO", "RWTP", "RXO", "RXRX", "RXST", "RXT", "RY", "RYAAY", "RYAM", "RYAN", "RYDE", "RYET", "RYI", "RYM", "RYN", "RYOJ", "RYTM", "RZB", "RZC", "RZLT", "RZLV", "RZLVW", "S", "SA", "SABA", "SABR", "SABS", "SABSW", "SACH", "SACH^A", "SAFE", "SAFT", "SAFX", "SAGT", "SAH", "SAIA", "SAIC", "SAIH", "SAIHW", "SAIL", "SAJ", "SAM", "SAMG", "SAN", "SANA", "SANG", "SANM", "SAP", "SAR", "SARO", "SAT", "SATA", "SATL", "SATLW", "SATS", "SAVA", "SAY", "SAZ", "SB", "SB^C", "SB^D", "SBAC", "SBC", "SBCF", "SBCWW", "SBDS",
"SBET", "SBEV", "SBFG", "SBFM", "SBGI", "SBH", "SBI", "SBLK", "SBLX", "SBR", "SBRA", "SBS", "SBSI", "SBSW", "SBUX", "SBXD", "SCAG", "SCCD", "SCCE", "SCCF", "SCCG", "SCCO", "SCD", "SCE^G", "SCE^J", "SCE^K", "SCE^L", "SCE^M", "SCE^N", "SCHL", "SCHW", "SCHW^D", "SCHW^J", "SCI", "SCKT", "SCL", "SCLX", "SCLXW", "SCM", "SCNI", "SCNX", "SCOR", "SCS", "SCSC", "SCVL", "SCWO", "SCYX", "SD", "SDA", "SDAWW", "SDGR", "SDHC", "SDHI", "SDHIR", "SDHIU", "SDHY", "SDOT", "SDRL", "SDST", "SDSTW", "SE", "SEAL^A", "SEAL^B", "SEAT", "SEATW", "SEB", "SEDG", "SEE", "SEED", "SEER", "SEG", "SEGG", "SEI", "SEIC", "SELF", "SELX", "SEM", "SEMR", "SENEA", "SENEB", "SENS", "SEPN", "SER", "SERA", "SERV", "SES", "SEV", "SEVN", "SEVNR", "SEZL", "SF", "SF^B", "SF^C", "SF^D", "SFB", "SFBC", "SFBS", "SFD", "SFHG", "SFIX", "SFL", "SFM", "SFNC", "SFST", "SFWL", "SG", "SGA", "SGBX", "SGC", "SGD", "SGHC", "SGHT", "SGI", "SGLY", "SGML", "SGMO", "SGMT", "SGN", "SGRP", "SGRY", "SGU", "SHAK", "SHBI", "SHC", "SHCO", "SHEL", "SHEN", "SHFS", "SHFSW", "SHG", "SHIM", "SHIP", "SHLS", "SHMD", "SHMDW", "SHO", "SHO^H", "SHO^I", "SHOO", "SHOP", "SHPH", "SHW", "SI", "SIBN", "SID", "SIDU", "SIEB", "SIF", "SIFY", "SIG", "SIGA", "SIGI", "SIGIP", "SII", "SILA", "SILC", "SILO", "SIM", "SIMA", "SIMAW", "SIMO", "SINT", "SION", "SIRI", "SITC", "SITE", "SITM", "SJ", "SJM", "SJT", "SKBL", "SKE", "SKIL", "SKIN", "SKK", "SKLZ", "SKM", "SKT", "SKWD", "SKY", "SKYE", "SKYH", "SKYQ", "SKYT", "SKYW", "SKYX", "SLAB", "SLAI", "SLB", "SLDB", "SLDE", "SLDP", "SLDPW", "SLE", "SLF", "SLG", "SLG^I", "SLGB", "SLGL", "SLGN", "SLI", "SLM", "SLMBP", "SLMT", "SLN", "SLND", "SLNG", "SLNH", "SLNHP", "SLNO", "SLP", "SLQT", "SLRC", "SLRX", "SLS", "SLSN", "SLSR", "SLVM", "SLXN", "SLXNW", "SM", "SMA", "SMBC", "SMBK", "SMC", "SMCI", "SMFG", "SMG", "SMHI", "SMID", "SMLR", "SMMT", "SMRT", "SMSI", "SMTC", "SMTI", "SMTK", "SMWB", "SMX", "SMXT", "SMXWW", "SN", "SNA", "SNAL", "SNAP", "SNBR", "SNCR", "SNCY", "SND", "SNDA", "SNDK", "SNDL", "SNDR", "SNDX", "SNES", "SNEX", "SNFCA", "SNGX", "SNN", "SNOA", "SNOW", "SNPS", "SNSE", "SNT", "SNTG", "SNTI", "SNV", "SNV^D", "SNV^E", "SNWV", "SNX", "SNY", "SNYR", "SO", "SOAR", "SOBO", "SOBR", "SOC", "SOCA", "SOCAW", "SOFI", "SOGP", "SOHO", "SOHOB", "SOHON", "SOHOO", "SOHU", "SOJC", "SOJD", "SOJE", "SOJF", "SOL", "SOLS", "SOLV", "SOMN", "SON", "SOND", "SONDW", "SONM", "SONN", "SONO", "SONY", "SOPA", "SOPH", "SOR", "SORA", "SOS", "SOTK", "SOUL", "SOUN", "SOUNW", "SOWG", "SPAI", "SPB", "SPCB", "SPCE", "SPE", "SPE^C", "SPEG", "SPEGR", "SPEGU", "SPFI", "SPG", "SPG^J", "SPGI", "SPH", "SPHL", "SPHR", "SPIR", "SPKL", "SPKLW", "SPMA", "SPMC", "SPME", "SPNS", "SPNT", "SPNT^B", "SPOK", "SPOT", "SPPL", "SPR", "SPRB", "SPRC", "SPRO", "SPRU", "SPRY", "SPSC", "SPT", "SPWH", "SPWR", "SPWRW", "SPXC", "SPXX", "SQFT", "SQFTP", "SQFTW", "SQM", "SQNS", "SR", "SR^A", "SRAD", "SRBK", "SRCE", "SRDX", "SRE", "SREA", "SRFM", "SRG", "SRG^A", "SRI", "SRL", "SRPT", "SRRK", "SRTA", "SRTAW", "SRTS", "SRV", "SRXH", "SRZN", "SRZNW", "SSB", "SSBI", "SSD", "SSEA", "SSEAU", "SSII", "SSKN", "SSL", "SSM", "SSNC", "SSP", "SSRM", "SSSS", "SSSSL", "SST", "SSTI", "SSTK", "SSYS", "ST", "STAA", "STAG", "STAI", "STAK", "STBA", "STC", "STE", "STEC", "STEL", "STEM", "STEP", "STEW", "STEX", "STFS", "STG", "STGW", "STHO", "STI", "STIM", "STK", "STKE", "STKH", "STKL", "STKS", "STLA", "STLD", "STM", "STN", "STNE", "STNG", "STOK", "STRA", "STRC", "STRD", "STRF", "STRK", "STRL", "STRO", "STRR", "STRRP", "STRS", "STRT", "STRW", "STRZ", "STSS", "STSSW", "STT", "STT^G", "STTK", "STUB", "STVN", "STWD", "STX", "STXS", "STZ", "SU", "SUGP", "SUI", "SUIG", "SUN", "SUNC", "SUNE", 
"SUNS", "SUPN", "SUPV", "SUPX", "SURG", "SUUN", "SUZ", "SVAC", "SVACU", "SVC", "SVCCU", "SVCCW", "SVCO", "SVM", "SVRA", "SVRE", "SVREW", "SVV", "SW", "SWAG", "SWAGW", "SWBI", "SWIM", "SWK", "SWKH", "SWKHL", "SWKS", "SWVL", "SWVLW", "SWX", "SWZ", "SXC", "SXI", "SXT", "SXTC", "SXTP", "SXTPW", "SY", "SYBT", "SYBX", "SYF", "SYF^A", "SYF^B", "SYK", "SYM", "SYNA", "SYNX", "SYPR", "SYRE", "SYY", "SZZL", "SZZLR", "SZZLU", "T", "T^A", "T^C", "TAC", "TACH", "TACHU", "TACHW", "TACO", "TACOU", "TACOW", "TACT", "TAIT", "TAK", "TAL", "TALK", "TALKW", "TALO", "TANH", "TAOP", "TAOX", "TAP", "TARA", "TARS", "TASK", "TATT", "TAVI", "TAYD", "TBB", "TBBB", "TBBK", "TBCH", "TBH", "TBHC", "TBI", "TBLA", "TBLAW", "TBLD", "TBMC", "TBMCR", "TBN", "TBPH", "TBRG", "TC", "TCBI", "TCBIO", "TCBK", "TCBS", "TCBX", "TCGL", "TCI", "TCMD", "TCOM", "TCPA", "TCPC", "TCRT", "TCRX", "TCX", "TD", "TDAC", "TDACW", "TDC", "TDF", "TDG", "TDIC", "TDOC", "TDS", "TDS^U", "TDS^V", "TDTH", "TDUP", "TDW", "TDWDU", "TDY", "TE", "TEAD", "TEAM", "TECH", "TECK", "TECTP", "TECX", "TEF", "TEI", "TEL", "TELA", "TELO", "TEM", "TEN", "TEN^E", "TEN^F", "TENB", "TENX", "TEO", "TER", "TERN", "TEVA", "TEX", "TFC", "TFC^I", "TFC^O", "TFC^R", "TFII", "TFIN", "TFIN^", "TFPM", "TFSA", "TFSL", "TFX", "TG", "TGB", "TGE", "TGEN", "TGHL", "TGL", "TGLS", "TGNA", "TGS", "TGT", "TGTX", "TH", "THAR", "THC", "THCH", "THFF", "THG", "THH", "THM", "THO", "THQ", "THR", "THRM", "THRY", "THS", "THW", "TIC", "TIGO", "TIGR", "TIL", "TILE", "TIMB", "TIPT", "TIRX", "TISI", "TITN", "TIVC", "TJX", "TK", "TKC", "TKLF", "TKNO", "TKO", "TKR", "TLF", "TLIH", "TLK", "TLN", "TLNC", "TLNCU", "TLNCW", "TLPH", "TLRY", "TLS", "TLSA", "TLSI", "TLSIW", "TLX", "TLYS", "TM", "TMC", "TMCI", "TMCWW", "TMDE", "TMDX", "TME", "TMHC", "TMO", "TMP", "TMQ", "TMUS", "TMUSI", "TMUSL", "TMUSZ", "TNC", "TNDM", "TNET", "TNGX", "TNK", "TNL", "TNMG", "TNON", "TNONW", "TNXP", "TNYA", "TOI", "TOIIW", "TOL", "TOMZ", "TONX", "TOON", "TOP", "TOPP", "TOPS", "TORO", "TOST", "TOUR", "TOVX", "TOWN", "TOYO", "TPB", "TPC", "TPCS", "TPET", "TPG", "TPGXL", "TPH", "TPL", "TPR", "TPST", "TPTA", "TPVG", "TR", "TRAK", "TRAW", "TRC", "TRDA", "TREE", "TREX", "TRGP", "TRI", "TRIB", "TRIN", "TRINI", "TRINZ", "TRIP", "TRMB", "TRMD", "TRMK", "TRN", "TRNO", "TRNR", "TRNS", "TRON", "TROO", "TROW", "TROX", "TRP", "TRS", "TRSG", "TRST", "TRT", "TRTN^A", "TRTN^B", "TRTN^C", "TRTN^D", "TRTN^E", "TRTN^F", "TRTX", "TRTX^C", "TRU", "TRUE", "TRUG", "TRUP", "TRV", "TRVG", "TRVI", "TRX", "TS", "TSAT", "TSBK", "TSCO", "TSE", "TSEM", "TSHA", "TSI", "TSLA", "TSLX", "TSM", "TSN", "TSQ", "TSSI", "TT", "TTAM", "TTAN", "TTC", "TTD", "TTE", "TTEC", "TTEK", "TTGT", "TTI", "TTMI", "TTRX", "TTSH", "TTWO", "TU", "TURB", "TUSK", "TUYA", "TV", "TVA", "TVACU", "TVACW", "TVAI", "TVC", "TVE", "TVGN", "TVGNW", "TVRD", "TVTX", "TW", "TWFG", "TWG", "TWI", "TWIN", "TWLO", "TWN", "TWNP", "TWO", "TWO^A", "TWO^B", "TWO^C", "TWOD", "TWST", "TX", "TXG", "TXMD", "TXN", "TXNM", "TXO", "TXRH", "TXT", "TY", "TY^", "TYG", "TYGO", "TYL", "TYRA", "TZOO", "TZUP", "U", "UA", "UAA", "UAL", "UAMY", "UAN", "UAVS", "UBCP", "UBER", "UBFO", "UBS", "UBSI", "UBXG", "UCAR", "UCB", "UCL", "UCTT", "UDMY", "UDR", "UE", "UEC", "UEIC", "UFCS", "UFG", "UFI", "UFPI", "UFPT", "UG", "UGI", "UGP", "UGRO", "UHAL", "UHG", "UHGWW", "UHS", "UHT", "UI", "UIS", "UK", "UKOMW", "UL", "ULBI", "ULCC", "ULH", "ULS", "ULTA", "ULY", "UMAC", "UMBF", "UMBFO", "UMC", "UMH", "UMH^D", "UNB", "UNCY", "UNF", "UNFI", "UNH", "UNIT", "UNM", "UNMA", "UNP", "UNTY", "UOKA", "UONE", "UONEK", "UP", "UPB", "UPBD", "UPC", "UPLD", "UPS", "UPST", "UPWK", "UPXI", "URBN", "URG", "URGN", "URI", 
"UROY", "USA", "USAC", "USAR", "USARW", "USAS", "USAU", "USB", "USB^A", "USB^H", "USB^P", "USB^Q", "USB^R", "USB^S", "USBC", "USCB", "USEA", "USEG", "USFD", "USGO", "USGOW", "USIO", "USLM", "USNA", "USPH", "UTF", "UTG", "UTHR", "UTI", "UTL", "UTMD", "UTSI", "UTZ", "UUU", "UUUU", "UVE", "UVSP", "UVV", "UWMC", "UXIN", "UYSC", "UYSCR", "UZD", "UZE", "UZF", "V", "VABK", "VAC", "VACH", "VACHW", "VAL", "VALE", "VALN", "VALU", "VANI", "VATE", "VBF", "VBIX", "VBNK", "VC", "VCEL", "VCIC", "VCICU", "VCICW", "VCIG", "VCTR", "VCV", "VCYT", "VECO", "VEEA", "VEEAW", "VEEE", "VEEV", "VEL", "VELO", "VENU", "VEON", "VERA", "VERI", "VERO", "VERU", "VERX", "VET", "VFC", "VFF", "VFL", "VFS", "VG", "VGAS", "VGI", "VGM", "VGZ", "VHC", "VHI", "VIA", "VIASP", "VIAV", "VICI", "VICR", "VIK", "VINP", "VIOT", "VIPS", "VIR", "VIRC", "VIRT", "VIST", "VITL", "VIV", "VIVK", "VIVS", "VKI", "VKQ", "VKTX", "VLGEA", "VLN", "VLO", "VLRS", "VLT", "VLTO", "VLY", "VLYPN", "VLYPO", "VLYPP", "VMAR", "VMC", "VMD", "VMEO", "VMI", "VMO", "VNCE", "VNDA", "VNET", "VNME", "VNMEU", "VNO", "VNO^L", "VNO^M", "VNO^N", "VNO^O", "VNOM", "VNRX", "VNT", "VNTG", "VOC", "VOD", "VOR", "VOXR", "VOYA", "VOYA^B", "VOYG", "VPG", "VPV", "VRA", "VRAR", "VRAX", "VRCA", "VRDN", "VRE", "VREX", "VRM", "VRME", "VRNS", "VRNT", "VRRM", "VRSK", "VRSN", "VRT", "VRTS", "VRTX", "VS", "VSA", "VSAT", "VSCO", "VSEC", "VSEE", "VSEEW", "VSH", "VSME", "VSSYW", "VST", "VSTA", "VSTD", "VSTM", "VSTS", "VTAK", "VTEX", "VTGN", "VTLE", "VTMX", "VTN", "VTOL", "VTR", "VTRS", "VTS", "VTSI", "VTVT", "VTYX", "VUZI", "VVOS", "VVPR", "VVR", "VVV", "VVX", "VWAV", "VWAVW", "VYGR", "VYNE", "VYX", "VZ", "VZLA", "W", "WAB", "WABC", "WAFD", "WAFDP", "WAFU", "WAI", "WAL", "WAL^A", "WALD", "WALDW", "WASH", "WAT", "WATT", "WAVE", "WAY", "WB", "WBD", "WBI", "WBS", "WBS^F", "WBS^G", "WBTN", "WBUY", "WBX", "WCC", "WCN", "WCT", "WD", "WDAY", "WDC", "WDFC", "WDH", "WDI", "WDS", "WEA", "WEAV", "WEC", "WELL", "WEN", "WENN", "WENNU", "WERN", "WES", "WEST", "WETH", "WETO", "WEX", "WEYS", "WF", "WFC", "WFC^A", "WFC^C", "WFC^D", "WFC^L", "WFC^Y", "WFC^Z", "WFCF", "WFF", "WFG", "WFRD", "WGO", "WGRX", "WGS", "WGSWW", "WH", "WHD", "WHF", "WHFCL", "WHG", "WHLR", "WHLRD", "WHLRL", "WHLRP", "WHR", "WHWK", "WIA", "WILC", "WIMI", "WINA", "WING", "WIT", "WIW", "WIX", "WK", "WKC", "WKEY", "WKHS", "WKSP", "WLAC", "WLACU", "WLACW", "WLDN", "WLDS", "WLDSW", "WLFC", "WLK", "WLKP", "WLY", "WLYB", "WM", "WMB", "WMG", "WMK", "WMS", "WMT", "WNC", "WNEB", "WNW", "WOK", "WOLF", "WOOF", "WOR", "WORX", "WOW", "WPC", "WPM", "WPP", "WPRT", "WRAP", "WRB", "WRB^E", "WRB^F", "WRB^G", "WRB^H", "WRBY", "WRD", "WRLD", "WRN", "WS", "WSBC", "WSBCO", "WSBCP", "WSBF", "WSBK", "WSC", "WSFS", "WSM", "WSO", "WSO/B", "WSR", "WST", "WSTNU", "WT", "WTBA", "WTF", "WTFC", "WTFCN", "WTGUR", "WTI", "WTM", "WTO", "WTRG", "WTS", "WTTR", "WTW", "WU", "WULF", "WVE", "WVVI", "WVVIP", "WW", "WWD", "WWR", "WWW", "WXM", "WY", "WYFI", "WYHG", "WYNN", "WYY", "XAIR", "XBIO", "XBIT", "XBP", "XBPEW", "XCH", "XCUR", "XEL", "XELB", "XELLL", "XENE", "XERS", "XFLT", "XFOR", "XGN", "XHG", "XHLD", "XHR", "XIFR", "XLO", "XMTR", "XNCR", "XNET", "XOM", "XOMA", "XOMAO", "XOMAP", "XOS", "XOSWW", "XP", "XPEL", "XPER", "XPEV", "XPL", "XPO", "XPOF", "XPON", "XPRO", "XRAY", "XRPC", "XRPN", "XRPNU", "XRPNW", "XRTX", "XRX", "XTIA", "XTKG", "XTLB", "XTNT", "XWEL", "XWIN", "XXII", "XYF", "XYL", "XYZ", "XZO", "YAAS", "YALA", "YB", "YCBD", "YCY", "YDDL", "YDES", "YDESW", "YDKG", "YELP", "YETI", "YEXT", "YGMZ", "YHC", "YHGJ", "YHNA", "YHNAR", "YI", "YIBO", "YJ", "YMAT", "YMM", "YMT", "YORW", "YOU", "YOUL", "YPF", "YQ", "YRD", "YSG", "YSXT", "YTRA", 
"YUM", "YUMC", "YXT", "YYAI", "YYGH", "Z", "ZBAI", "ZBAO", "ZBH", "ZBIO", "ZBRA", "ZCMD", "ZD", "ZDAI", "ZDGE", "ZENA", "ZENV", "ZEO", "ZEOWW", "ZEPP", "ZETA", "ZEUS", "ZG", "ZGM", "ZGN", "ZH", "ZIM", "ZION", "ZIONP", "ZIP", "ZJK", "ZJYL", "ZK", "ZKH", "ZKIN", "ZLAB", "ZM", "ZNB", "ZNTL", "ZONE", "ZOOZ", "ZOOZW", "ZS", "ZSPC", "ZTEK", "ZTO", "ZTR", "ZTS", "ZUMZ", "ZURA", "ZVIA", "ZVRA", "ZWS", "ZYBT", "ZYME", "ZYXI",
#US500
"A", "AAPL", "ABBV", "ABNB", "ABT", "ACGL", "ACN", "ADBE", "ADI", "ADM", "ADP", "ADSK", "AEE", "AEP", "AES", "AFL", "AIG", "AIZ", "AJG", "AKAM", "ALB", "ALGN", "ALL", "ALLE", "AMAT", "AMCR", "AMD", "AME", "AMGN", "AMP", "AMT", "AMZN", "ANET", "AON", "AOS", "APA", "APD", "APH", "APO", "APP", "APTV", "ARE", "ATO", "AVB", "AVGO", "AVY", "AWK", "AXON", "AXP", "AZO", "BA", "BAC", "BALL", "BAX", "BBY", "BDX", "BEN", "BF.B", "BG", "BIIB", "BK", "BKNG", "BKR", "BLDR", "BLK", "BMY", "BR", "BRK.B", "BRO", "BSX", "BX", "BXP", "C", "CAG", "CAH", "CARR", "CAT", "CB", "CBOE", "CBRE", "CCI", "CCL", "CDNS", "CDW", "CEG", "CF", "CFG", "CHD", "CHRW", "CHTR", "CI", "CINF", "CL", "CLX", "CMCSA", "CME", "CMG", "CMI", "CMS", "CNC", "CNP", "COF", "COIN", "COO", "COP", "COR", "COST", "CPAY", "CPB", "CPRT", "CPT", "CRL", "CRM", "CRWD", "CSCO", "CSGP", "CSX", "CTAS", "CTRA", "CTSH", "CTVA", "CVS", "CVX", "D", "DAL", "DASH", "DAY", "DD", "DDOG", "DE", "DECK", "DELL", "DG", "DGX", "DHI", "DHR", "DIS", "DLR", "DLTR", "DOC", "DOV", "DOW", "DPZ", "DRI", "DTE", "DUK", "DVA", "DVN", "DXCM", "EA", "EBAY", "ECL", "ED", "EFX", "EG", "EIX", "EL", "ELV", "EME", "EMR", "EOG", "EPAM", "EQIX", "EQR", "EQT", "ERIE", "ES", "ESS", "ETN", "ETR", "EVRG", "EW", "EXC", "EXE", "EXPD", "EXPE", "EXR", "F", "FANG", "FAST", "FCX", "FDS", "FDX", "FE", "FFIV", "FISV", "FICO", "FIS", "FITB", "FOX", "FOXA", "FRT", "FSLR", "FTNT", "FTV", "GD", "GDDY", "GE", "GEHC", "GEN", "GEV", "GILD", "GIS", "GL", "GLW", "GM", "GNRC", "GOOG", "GOOGL", "GPC", "GPN", "GRMN", "GS", "GWW", "HAL", "HAS", "HBAN", "HCA", "HD", "HIG", "HII", "HLT", "HOLX", "HON", "HOOD", "HPE", "HPQ", "HRL", "HSIC", "HST", "HSY", "HUBB", "HUM", "HWM", "IBKR", "IBM", "ICE", "IDXX", "IEX", "IFF", "INCY", "INTC", "INTU", "INVH", "IP", "IPG", "IQV", "IR", "IRM", "ISRG", "IT", "ITW", "IVZ", "J", "JBHT", "JBL", "JCI", "JKHY", "JNJ", "JPM", "K", "KDP", "KEY", "KEYS", "KHC", "KIM", "KKR", "KLAC", "KMB", "KMI", "KO", "KR", "KVUE", "L", "LDOS", "LEN", "LH", "LHX", "LII", "LIN", "LKQ", "LLY", "LMT", "LNT", "LOW", "LRCX", "LULU", "LUV", "LVS", "LW", "LYB", "LYV", "MA", "MAA", "MAR", "MAS", "MCD", "MCHP", "MCK", "MCO", "MDLZ", "MDT", "MET", "META", "MGM", "MHK", "MKC", "MLM", "MMC", "MMM", "MNST", "MO", "MOH", "MOS", "MPC", "MPWR", "MRK", "MRNA", "MS", "MSCI", "MSFT", "MSI", "MTB", "MTCH", "MTD", "MU", "NCLH", "NDAQ", "NDSN", "NEE", "NEM", "NFLX", "NI", "NKE", "NOC", "NOW", "NRG", "NSC", "NTAP", "NTRS", "NUE", "NVDA", "NVR", "NWS", "NWSA", "NXPI", "O", "ODFL", "OKE", "OMC", "ON", "ORCL", "ORLY", "OTIS", "OXY", "PANW", "PAYC", "PAYX", "PCAR", "PCG", "PEG", "PEP", "PFE", "PFG", "PG", "PGR", "PH", "PHM", "PKG", "PLD", "PLTR", "PM", "PNC", "PNR", "PNW", "PODD", "POOL", "PPG", "PPL", "PRU", "PSA", "PSKY", "PSX", "PTC", "PWR", "PYPL", "Q", "QCOM", "RCL", "REG", "REGN", "RF", "RJF", "RL", "RMD", "ROK", "ROL", "ROP", "ROST", "RSG", "RTX", "RVTY", "SBAC", "SBUX", "SCHW", "SHW", "SJM", "SLB", "SMCI", "SNA", "SNPS", "SO", "SOLS", "SOLV", "SPG", "SPGI", "SRE", "STE", "STLD", "STT", "STX", "STZ", "SW", "SWK", "SWKS", "SYF", "SYK", "SYY", "T", "TAP", "TDG", "TDY", "TECH", "TEL", "TER", "TFC", "TGT", "TJX", "TKO", "TMO", "TMUS", "TPL", "TPR", "TRGP", "TRMB", "TROW", "TRV", "TSCO", "TSLA", "TSN", "TT", "TTD", "TTWO", "TXN", "TXT", "TYL", "UAL", "UBER", "UDR", "UHS", "ULTA", "UNH", "UNP", "UPS", "URI", "USB", "V", "VICI", "VLO", "VLTO", "VMC", "VRSK", "VRSN", "VRTX", "VST", "VTR", "VTRS", "VZ", "WAB", "WAT", "WBD", "WDAY", "WDC", "WEC", "WELL", "WFC", "WM", "WMB", "WMT", "WRB", "WSM", "WST", "WTW", "WY", "WYNN", "XEL", "XOM", "XYL", "XYZ", "YUM", "ZBH", "ZBRA", "ZTS",
#Sectors
"XLY", "IWM", "DIA", "SPY", "XLI", "QQQ", "XLK", "SMH", "XLRE", "XLE", "KRE", "DXY", "GDX", "XLP", "XLF", "XLU", "XLV",

],

    "US 30 (Dow)": ["AMGN", "AMZN", "CRM", "CVX", "DIS", "GS", "HD", "IBM", "JNJ", "JPM", "MCD", "MMM", "MRK", "NKE", "PG", "TRV", "UNH", "VZ", "WMT", "V", "KO", "SHW", "AXP", "BA", "CAT", "CSCO", "AAPL", "HON", "MSFT", "NVDA"],
    
    "ETF Sectors": ["EWA", "EWC", "EWG", "EWH", "EWJ", "EWL", "EWM", "EWP", "EWS", "EWT", "EWU", "EWW", "EWY", "EWZ", "EZA", "FXI", "DXJ", "EPI", "PIN", "IDX", "EWI", "XAR", "XSD", "BLCN", "ROKT", "CRAK", "PSI", "IEO", "FTXL", "ARKK", "QTUM", "PRN", "ARKW", "PPA", "BLOK", "ITA", "SOXX", "PKB", "CSD", "FPX", "FITE", "ECH", "EZA", "QMOM", "SLX", "JSMD", "AIRR", "URA", "PEXL", "JSML", "RSPG", "COPX", "GRPM", "IDX", "SMH", "SIXG", "FNY", "COLO", "XNTK", "GRID", "XMMO", "QLD", "NANR", "RFV", "SPHB", "PSCI", "CARZ", "RING", "CHIQ", "VFMO", "FYC", "XMHQ", "PAVE", "VDE", "PIZ", "XME", "FAD", "ROBO", "SMLF", "RZV", "EPU", "IXC", "AIA", "IDOG", "FTEC", "XLE", "PICK", "VGT", "USCI", "XLK", "SDCI", "FDD", "VOT", "IGM", "AADR", "RWK", "BFOR", "FTGC", "EQRR", "PRFZ", "IWP", "IYW", "VB", "ISCF", "PSC", "GDX", "QGRO", "GVAL", "GSSC", "FNDE", "FDMO", "IETC", "PXH", "IJJ", "EFAS", "EMQQ", "RWJ", "EYLD", "JHMM", "RAAX", "OMFS"],
    
    "Crypto": ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","DOT-USD","MATIC-USD"],
    
    "Forex": ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X"],
    
    "Indices": ["^GSPC","^DJI","^IXIC","^RUT","^VIX"]
}

# -----------------------------
# PREMIUM UI STYLING
# -----------------------------
def inject_custom_css():
    st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        
        /* Metric Cards */
        [data-testid="stMetric"] {
            background-color: #1e2127;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #2d313a;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #14171e;
            border-right: 1px solid #2d313a;
        }
        
        /* Custom Buttons */
        .stButton>button {
            border-radius: 20px;
            font-weight: 600;
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #1e2127;
            border-radius: 5px;
            padding: 10px 20px;
            color: #c0c0c0;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #ff4b4b;
            color: white;
        }
        
        /* Expander Headers */
        .streamlit-expanderHeader {
            background-color: #1e2127 !important;
            border-radius: 5px !important;
        }
        
        /* Dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid #2d313a;
        }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# CONFIGURATION
# -----------------------------
HIST_DAYS = 180
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14
OBV_LOOKBACK = 14
VOLUME_SPIKE_MULT = 1.5

# Multi-timeframe config
MTF_TIMEFRAMES = ["1d", "4h", "1h"]
MTF_CONFIRM_THRESHOLD = 2
MTF_POSITIVE_PRICE_SCORE = 60.0

# Buy-the-Dip config
BTD_LOOKBACK_DAYS = 20
BTD_MIN_PULLBACK = 0.02
BTD_MAX_PULLBACK = 0.08
BTD_REQUIRE_DAILY_UPTREND = True

# Score weights (Technical)
SCORES_CONFIG = {
    "EQUITY": {"price": 0.40, "flow": 0.35, "fund": 0.25},
    "ETF": {"price": 0.45, "flow": 0.45, "fund": 0.10},
    "INDEX": {"price": 0.70, "flow": 0.00, "fund": 0.30},
    "COMMODITY": {"price": 0.80, "flow": 0.20, "fund": 0.00},
    "CRYPTOCURRENCY": {"price": 0.75, "flow": 0.25, "fund": 0.00},
    "CURRENCY": {"price": 0.80, "flow": 0.20, "fund": 0.00},
    "UNKNOWN": {"price": 0.40, "flow": 0.35, "fund": 0.25}
}
INST_FLOW_WEIGHT = 0.10

# -----------------------------
# TECHNICAL ANALYSIS HELPERS
# -----------------------------
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period, min_periods=period).mean()
    ma_down = down.rolling(period, min_periods=period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def compute_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iat[i] > df['Close'].iat[i-1]:
            obv.append(obv[-1] + int(df['Volume'].iat[i]) if 'Volume' in df.columns else obv[-1])
        elif df['Close'].iat[i] < df['Close'].iat[i-1]:
            obv.append(obv[-1] - int(df['Volume'].iat[i]) if 'Volume' in df.columns else obv[-1])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def safe_div(a,b,default=np.nan):
    try:
        return a/b if b else default
    except Exception:
        return default

def get_history(ticker, timeframe='1d', days=HIST_DAYS):
    t = yf.Ticker(ticker)
    if timeframe == '1d':
        interval = '1d'
        period = f"{days}d"
    elif timeframe == '4h':
        interval = '60m' # yfinance 4h is flaky, use 60m and resample if needed, or just use 60m as proxy for intraday trend
        period = "60d" 
    elif timeframe == '1h':
        interval = '1h'
        period = "60d"
    else:
        interval = timeframe
        period = f"{days}d"
    
    try:
        hist = t.history(period=period, interval=interval, actions=False)
        if hist is None or hist.empty:
            return pd.DataFrame()
        return hist.dropna(subset=['Close'])
    except Exception:
        return pd.DataFrame()

def compute_technical_metrics_from_hist(hist):
    if hist.empty: return {}
    close = hist['Close']
    low = hist['Low'] if 'Low' in hist.columns else close
    vol = hist['Volume'] if 'Volume' in hist.columns else pd.Series([0]*len(hist), index=hist.index)

    tech = {}
    tech['last_close'] = float(close.iloc[-1])
    tech['ema_fast'] = float(ema(close, EMA_FAST).iloc[-1])
    tech['ema_slow'] = float(ema(close, EMA_SLOW).iloc[-1])
    tech['ema_cross'] = int(tech['ema_fast'] > tech['ema_slow'])
    tech['price_above_ema_slow'] = int(close.iloc[-1] > tech['ema_slow'])

    r = rsi(close, RSI_PERIOD)
    tech['rsi'] = float(r.iloc[-1]) if not r.isna().all() else 50.0
    tech['rsi_rising'] = int(r.iloc[-1] > r.iloc[-3]) if len(r) >= 3 else 0

    try:
        lows = low.dropna().iloc[-5:]
        tech['higher_lows_3'] = int(len(lows) >= 3 and lows.iloc[-1] > lows.iloc[-2] > lows.iloc[-3])
    except Exception:
        tech['higher_lows_3'] = 0

    obv = compute_obv(hist)
    tech['obv_latest'] = float(obv.iloc[-1])
    if len(obv) >= OBV_LOOKBACK:
        y = obv.iloc[-OBV_LOOKBACK:].values
        x = np.arange(len(y))
        if np.all(np.isfinite(y)):
            m = np.polyfit(x, y, 1)[0]
            tech['obv_slope'] = float(m)
            tech['obv_slope_pos'] = int(m > 0)
        else:
            tech['obv_slope'] = 0.0
            tech['obv_slope_pos'] = 0
    else:
        tech['obv_slope'] = 0.0
        tech['obv_slope_pos'] = 0

    avg30 = vol.rolling(30, min_periods=5).mean().iloc[-1] if len(vol) >= 5 else (vol.mean() if len(vol)>0 else 0)
    tech['avg_vol_30'] = float(avg30 if not np.isnan(avg30) else 0.0)
    tech['today_vol'] = float(vol.iloc[-1]) if len(vol)>0 else 0.0
    today_up = int(close.iloc[-1] > close.iloc[-2]) if len(close) >= 2 else 0
    tech['vol_spike_up'] = int((tech['today_vol'] > VOLUME_SPIKE_MULT * tech['avg_vol_30']) and today_up)

    return tech



def compute_options_metrics(ticker):
    t = yf.Ticker(ticker)
    res = {
        'call_put_vol_ratio': np.nan,
        'call_put_oi_ratio': np.nan,
        'pcr_volume': np.nan,
        'pcr_oi': np.nan,
        'avg_call_iv': np.nan,
        'avg_put_iv': np.nan,
        'iv_skew': np.nan # Call IV / Put IV
    }
    try:
        exps = t.options
        if not exps: return res
        
        # Use nearest expiry for most relevant "now" sentiment
        ne = exps[0] 
        chain = t.option_chain(ne)
        calls = chain.calls
        puts = chain.puts
        
        # Volume & OI Aggregates
        cv = int(calls['volume'].fillna(0).sum()) if not calls.empty else 0
        pv = int(puts['volume'].fillna(0).sum()) if not puts.empty else 0
        coi = int(calls['openInterest'].fillna(0).sum()) if not calls.empty else 0
        poi = int(puts['openInterest'].fillna(0).sum()) if not puts.empty else 0
        
        res['call_put_vol_ratio'] = safe_div(cv, pv) # Kept for backward compatibility
        res['call_put_oi_ratio'] = safe_div(coi, poi)
        
        # Standard PCR (Put / Call)
        res['pcr_volume'] = safe_div(pv, cv)
        res['pcr_oi'] = safe_div(poi, coi)
        
        # Implied Volatility Aggregates (Volume Weighted preferred, but simple mean for robustness here)
        # Filter for reasonable IVs to avoid data junk (e.g., 0 or > 500%)
        if not calls.empty and 'impliedVolatility' in calls.columns:
            valid_calls = calls[(calls['impliedVolatility'] > 0) & (calls['impliedVolatility'] < 5)]
            if not valid_calls.empty:
                res['avg_call_iv'] = valid_calls['impliedVolatility'].mean()
                
        if not puts.empty and 'impliedVolatility' in puts.columns:
            valid_puts = puts[(puts['impliedVolatility'] > 0) & (puts['impliedVolatility'] < 5)]
            if not valid_puts.empty:
                res['avg_put_iv'] = valid_puts['impliedVolatility'].mean()
                
        # Skew: Higher Call IV relative to Put IV often implies bullish demand
        res['iv_skew'] = safe_div(res.get('avg_call_iv', np.nan), res.get('avg_put_iv', np.nan))
        
    except Exception:
        pass
    return res

def get_google_news_rss(query, max_items=5):
    """
    Fetches news from Google News RSS feed for a given query.
    Returns a list of dicts: {'title': ..., 'link': ..., 'pubDate': ...}
    """
    try:
        base_url = "https://news.google.com/rss/search?q={}&hl=en-US&gl=US&ceid=US:en"
        encoded_query = urllib.parse.quote(query)
        url = base_url.format(encoded_query)
        
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return []
            
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall('.//item')[:max_items]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            # Clean up title (Google News often adds " - Source" at the end)
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
                
            items.append({'title': title, 'link': link, 'pubDate': pubDate})
            
        return items
    except Exception as e:
        print(f"News fetch error for {query}: {e}")
        return []

def analyze_sentiment(news_items):
    """
    Analyzes sentiment of news headlines using simple keyword matching.
    Returns a score from 0 to 100 (50 is neutral).
    """
    if not news_items:
        return 50.0
        
    bullish_words = ["soar", "surge", "jump", "record", "beat", "gain", "profit", "bull", "growth", "high", "up", "buy", "outperform"]
    bearish_words = ["plunge", "drop", "miss", "fall", "crash", "loss", "bear", "debt", "risk", "low", "down", "sell", "underperform", "inflation", "recession"]
    
    score = 0
    total_matches = 0
    
    for item in news_items:
        title = item['title'].lower()
        
        # Simple count
        p_count = sum(1 for w in bullish_words if w in title)
        n_count = sum(1 for w in bearish_words if w in title)
        
        score += (p_count - n_count)
        total_matches += (p_count + n_count)
        
    # Normalize to -1 to 1 range (clamped)
    # If we found matches, we scale. If no matches, we stay neutral 0.
    final_score = 0.0
    if total_matches > 0:
        # Scale: A net score of +3 or -3 is considered very strong for 5 headlines
        final_score = max(-1.0, min(1.0, score / 3.0)) 
    
    # Map -1..1 to 0..100
    return 50 + (final_score * 50)

def score_options_sentiment(opt):
    """
    Returns a score 0-100 based on Options Sentiment.
    Bullish: Low PCR (Volume), High IV Skew (Call IV > Put IV).
    """
    score = 50.0 # Start neutral
    valid_metrics = 0
    
    # 1. Put/Call Ratio (Volume)
    # < 0.7 Bullish, > 1.0 Bearish
    pcr = opt.get('pcr_volume', np.nan)
    if np.isfinite(pcr):
        # Map PCR: 0.5 -> score 80? 1.5 -> score 20?
        # Logic: Lower is better.
        # 0.7 is fairly bullish. 1.0 is neutral. 1.3 is bearish.
        # Clamp between 0.4 and 1.6
        clamped_pcr = max(0.4, min(1.6, pcr))
        # Invert: (1.6 - 0.4) = 1.2 range. 
        # (1.6 - clamped) / 1.2 * 100
        pcr_score = ((1.6 - clamped_pcr) / 1.2) * 100
        score += (pcr_score - 50) # Add deviation from neutral
        valid_metrics += 1
        
    # 2. IV Skew (Call IV / Put IV)
    # > 1.0 Bullish (Calls more expensive), < 1.0 Bearish
    skew = opt.get('iv_skew', np.nan)
    if np.isfinite(skew):
        # Map: 1.2 -> Bullish, 0.8 -> Bearish
        clamped_skew = max(0.8, min(1.2, skew)) # Narrow range usually
        # (clamped - 0.8) / 0.4 * 100
        skew_score = ((clamped_skew - 0.8) / 0.4) * 100
        score += (skew_score - 50)
        valid_metrics += 1
        
    # Re-center
    # If we added 2 deviations, average them?
    # Simply: Base 50 + sum(deviations) / max(1, count) is safer but let's stick to accumulating "sentiment points" 
    # and clamping.
    
    final = max(0.0, min(100.0, score))
    return float(final)

def score_price_momentum(tech):
    w_ema = 0.35
    w_price = 0.25
    w_rsi = 0.20
    w_hl = 0.20
    score = 0.0
    score += w_ema * (1.0 if tech.get('ema_cross',0)==1 else 0.0)
    score += w_price * (1.0 if tech.get('price_above_ema_slow',0)==1 else 0.0)
    r = tech.get('rsi', 50.0)
    if r < 30: r_score = 0.0
    elif r > 80: r_score = 0.2
    else: r_score = max(0.0, 1.0 - abs(r-60)/30.0)
    if tech.get('rsi_rising',0): r_score = min(1.0, r_score*1.2)
    score += w_rsi * r_score
    score += w_hl * (1.0 if tech.get('higher_lows_3',0)==1 else 0.0)
    return float(score*100.0)

def score_volume_flow(tech, opt):
    w_vol_spike = 0.30
    w_obv = 0.30
    w_cp_vol = 0.20
    w_cp_oi = 0.20
    s = 0.0
    s += w_vol_spike * (1.0 if tech.get('vol_spike_up',0)==1 else 0.0)
    s += w_obv * (1.0 if tech.get('obv_slope_pos',0)==1 else 0.0)
    cpv = opt.get('call_put_vol_ratio', np.nan)
    cpoi = opt.get('call_put_oi_ratio', np.nan)
    
    if np.isfinite(cpv):
        mapped = max(0.0, min(1.0, cpv/2.0))
        s += w_cp_vol * mapped
    else:
        s += w_cp_vol * 0.5
        
    if np.isfinite(cpoi):
        mapped = max(0.0, min(1.0, cpoi/2.0))
        s += w_cp_oi * mapped
    else:
        s += w_cp_oi * 0.5
        
    total = w_vol_spike + w_obv + w_cp_vol + w_cp_oi
    return float(s/total*100.0)

def detect_buy_the_dip(ticker, tech, hist):
    if BTD_REQUIRE_DAILY_UPTREND:
        if not (tech.get('ema_cross',0) == 1 and tech.get('price_above_ema_slow',0) == 1):
            return False, 0.0
    
    last_close = tech.get('last_close', 0)
    if last_close == 0: return False, 0.0

    look = hist['Close'].iloc[-BTD_LOOKBACK_DAYS:] if len(hist) >= BTD_LOOKBACK_DAYS else hist['Close']
    recent_high = float(look.max())
    pullback = (recent_high - last_close) / recent_high if recent_high>0 else 0.0
    is_btd = (pullback >= BTD_MIN_PULLBACK) and (pullback <= BTD_MAX_PULLBACK)
    return bool(is_btd), pullback

# -----------------------------
# FUNDAMENTAL ANALYSIS HELPERS (MEET KEVIN)
# -----------------------------
def get_growth_metrics(ticker_obj):
    try:
        financials = ticker_obj.financials
        if financials.empty: return None, None, None
        
        # Revenue
        rev_key = 'Total Revenue' if 'Total Revenue' in financials.index else 'TotalRevenue'
        if rev_key not in financials.index: return None, None, None
        
        revenue = financials.loc[rev_key]
        if len(revenue) < 2: return None, None, None
        
        current_rev = revenue.iloc[0]
        prev_rev = revenue.iloc[1]
        revenue_growth = ((current_rev - prev_rev) / prev_rev) * 100

        # Opex
        opex_key = 'Total Operating Expenses' if 'Total Operating Expenses' in financials.index else 'Operating Expenses'
        opex_growth = None
        if opex_key in financials.index:
            opex = financials.loc[opex_key]
            if len(opex) >= 2:
                current_opex = opex.iloc[0]
                prev_opex = opex.iloc[1]
                opex_growth = ((current_opex - prev_opex) / prev_opex) * 100

        operating_leverage = False
        if opex_growth is not None:
            if revenue_growth > opex_growth:
                operating_leverage = True
        
        return revenue_growth, opex_growth, operating_leverage
    except Exception:
        return None, None, None

def analyze_meet_kevin(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    try:
        info = stock.info
    except Exception:
        return None
    
    if not info: return None

    # Check Quote Type - Only apply full fundamental analysis to Equities
    quote_type = info.get('quoteType', 'EQUITY') # Default to EQUITY if missing
    if quote_type not in ['EQUITY']:
        return {
            "score": 0,
            "max_score": 6,
            "results": {},
            "error": f"Fundamental analysis skipped for {quote_type}"
        }

    # Data
    gross_margins = info.get('grossMargins', 0) * 100
    total_cash = info.get('totalCash', 0)
    total_debt = info.get('totalDebt', 0)
    current_ratio = info.get('currentRatio', 0)
    peg_ratio = info.get('pegRatio', None)
    insider_ownership = info.get('heldPercentInsiders', 0) * 100
    
    net_cash_positive = total_cash > total_debt
    rev_growth, opex_growth, op_leverage = get_growth_metrics(stock)

    # Scoring
    score = 0
    max_score = 6
    results = {}

    # 1. Pricing Power
    if gross_margins > 40: 
        score += 1
        results['margins'] = {'pass': True, 'val': gross_margins, 'msg': "High (>40%)"}
    elif gross_margins > 20: 
        score += 0.5
        results['margins'] = {'pass': 'partial', 'val': gross_margins, 'msg': "Moderate (>20%)"}
    else:
        results['margins'] = {'pass': False, 'val': gross_margins, 'msg': "Low (<20%)"}

    # 2. Growth
    if rev_growth and rev_growth > 20:
        score += 1
        results['growth'] = {'pass': True, 'val': rev_growth, 'msg': "High (>20%)"}
    elif rev_growth and rev_growth > 10:
        score += 0.5
        results['growth'] = {'pass': 'partial', 'val': rev_growth, 'msg': "Moderate (>10%)"}
    else:
        val = rev_growth if rev_growth else 0
        results['growth'] = {'pass': False, 'val': val, 'msg': "Low (<10%)"}

    # 3. Operating Leverage
    if op_leverage:
        score += 1
        results['oplev'] = {'pass': True, 'msg': "Yes"}
    else:
        results['oplev'] = {'pass': False, 'msg': "No"}

    # 4. Balance Sheet
    if net_cash_positive:
        score += 1
        results['balance'] = {'pass': True, 'msg': "Net Cash +"}
    elif current_ratio > 1.5:
        score += 0.5
        results['balance'] = {'pass': 'partial', 'msg': "Safe Liq"}
    else:
        results['balance'] = {'pass': False, 'msg': "High Debt"}

    # 5. Valuation
    if peg_ratio and peg_ratio < 1.0 and peg_ratio > 0:
        score += 1
        results['val'] = {'pass': True, 'val': peg_ratio, 'msg': "Undervalued"}
    elif peg_ratio and peg_ratio < 1.5:
        score += 0.5
        results['val'] = {'pass': 'partial', 'val': peg_ratio, 'msg': "Fair"}
    else:
        val = peg_ratio if peg_ratio else 0
        results['val'] = {'pass': False, 'val': val, 'msg': "Expensive"}

    # 6. Insider Ownership
    if insider_ownership > 10:
        score += 1
        results['insider'] = {'pass': True, 'val': insider_ownership, 'msg': "High (>10%)"}
    elif insider_ownership > 5:
        score += 0.5
        results['insider'] = {'pass': 'partial', 'val': insider_ownership, 'msg': "Mod (>5%)"}
    else:
        results['insider'] = {'pass': False, 'val': insider_ownership, 'msg': "Low (<5%)"}

    return {
        "score": score,
        "max_score": max_score,
        "results": results
    }

# -----------------------------
# MAIN APP LOGIC
# -----------------------------
def analyze_ticker(ticker, run_fundamental=False):
    # 1. Technical Analysis
    hist = get_history(ticker, '1d')
    if hist.empty:
        return {"error": "No data"}
    
    tech = compute_technical_metrics_from_hist(hist)
    opt = compute_options_metrics(ticker)
    
    price_score = score_price_momentum(tech)
    flow_score = score_volume_flow(tech, opt)
    
    # New Options Score
    opt_score = score_options_sentiment(opt)
    
    # Simple weighting for Technical Score (Price + Flow)
    tech_final = (price_score * 0.6) + (flow_score * 0.4)
    
    # BTD
    is_btd, btd_pct = detect_buy_the_dip(ticker, tech, hist)
    
    # MTF (Simplified for speed - just check 1h)
    hist_1h = get_history(ticker, '1h')
    tech_1h = compute_technical_metrics_from_hist(hist_1h)
    price_score_1h = score_price_momentum(tech_1h)
    mtf_confirm = price_score_1h > 60

    result = {
        "ticker": ticker,
        "tech_score": round(tech_final, 1),
        "price_score": round(price_score, 1),
        "flow_score": round(flow_score, 1),
        "last_price": round(tech['last_close'], 2),
        "rsi": round(tech['rsi'], 1),
        "btd": is_btd,
        "mtf": mtf_confirm,
        "btd": is_btd,
        "mtf": mtf_confirm,
        "fundamental": None,
        "news": [],
        "opt_metrics": opt,
        "opt_score": round(opt_score, 1)
    }
    
    # 2. News Scanning (Lightweight)
    rec_news = get_google_news_rss(ticker)
    result['news'] = rec_news
    
    # 3. Sentiment Analysis
    sent_score = analyze_sentiment(rec_news)
    result['sent_score'] = round(sent_score, 1)

    # 4. Fundamental Analysis (Optional)
    fund_score_val = 50.0 # Neutral default
    fund_weight = 0.0
    
    if run_fundamental:
        fund_data = analyze_meet_kevin(ticker)
        if fund_data and "error" not in fund_data:
            result['fundamental'] = fund_data
            # Kevin Score is 0-6. Map to 0-100.
            # 6 -> 100, 3 -> 50, 0 -> 0
            fund_score_val = (fund_data['score'] / fund_data['max_score']) * 100
            fund_weight = 0.4
    
    # 5. Overall Conviction Score
    # Weights depend on if we have valid fundamentals
    tech_score = tech_final
    
    # Dynamic weighting
    w_tech = 0.4
    w_fund = 0.0
    w_news = 0.2
    w_opt = 0.0
    
    if fund_weight > 0:
        # Stock: 35% Tech, 35% Fund, 15% News, 15% Options
        w_tech = 0.35
        w_fund = 0.35
        w_news = 0.15
        w_opt = 0.15
    else:
        # Crypto/Asset: 60% Tech, 30% News, 10% Options (if avail) or redistribute
        w_tech = 0.7
        w_news = 0.3
        # If options data is sparse for crypto, we might ignore, but let's keep it small if exists? 
        # Actually Crypto options on yahoo are rare. Let's check validity of opt score.
        pass
        
    overall = (tech_score * w_tech) + (fund_score_val * w_fund) + (sent_score * w_news) + (opt_score * w_opt)
    result['overall_score'] = round(overall, 1)
            
    return result

# -----------------------------
# STREAMLIT UI
# -----------------------------
def main():
    inject_custom_css()
    
    st.title("🚀 Ultimate Market Scanner")
    st.markdown("Integrates **Advanced Technical Readiness**, **Options Sentiment**, and **Fundamental Analysis**.")
    
    # --- Sidebar Controls ---
    with st.sidebar:
        st.header("⚙️ Scanner Settings")
        
        # Asset Category
        asset_class = st.selectbox("Asset Class", list(PRESETS.keys()))
        
        tickers = []
        if asset_class == "Stocks (Manual)":
            default_tickers = "TSLA, NVDA, AAPL, PLTR, AMD, F, SPY, QQQ"
            ticker_input = st.text_area("Enter Tickers (comma separated)", value=default_tickers, height=100)
            tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]
        else:
            tickers = PRESETS[asset_class]
            st.info(f"Loaded {len(tickers)} tickers for {asset_class}")

        st.divider()
        run_fundamental = st.checkbox("Run Stock Fundamentals?", value=(asset_class in ["Stocks (Manual)", "S&P 500 Leaders", "US 30 (Dow)"]), 
                                    help="Fetches financial statements. Only works for Stocks.")
        
        run_btn = st.button("🚀 Start Scan", type="primary")

    # --- Dashboard Metrics (Market Pulse) ---
    col1, col2, col3, col4 = st.columns(4)
    # Placeholder for live market data (could fetch SPY/BTC real quick)
    col1.metric("S&P 500 (SPY)", "Loading...", border=True)
    col2.metric("Nasdaq (QQQ)", "Loading...", border=True)
    col3.metric("Bitcoin (BTC)", "Loading...", border=True)
    col4.metric("VIX", "Loading...", border=True)

    # --- Main Scanner Loop ---
    if run_btn:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers):
            status_text.text(f"Scanning {ticker}...")
            res = analyze_ticker(ticker, run_fundamental=run_fundamental)
            if "error" not in res:
                results.append(res)
            progress_bar.progress((i + 1) / len(tickers))
        
        status_text.empty()
        progress_bar.empty()
        
        if not results:
            st.warning("No results found.")
            return

        # Display Results
        display_results(results)

def display_results(results):
    # Convert to DataFrame for main view
    df_data = []
    
    for r in results:
        row = {
            "Ticker": r['ticker'],
            "Price": r['last_price'],
            "Conviction": r['overall_score'], # Raw score for sorting
            "Conviction Label": f"{'🐂' if r['overall_score'] >= 60 else '🐻' if r['overall_score'] <= 40 else '⚖️'} {r['overall_score']}",
            "Tech Score": r['tech_score'],
            "Options Score": r['opt_metrics'].get('opt_score', 0) if 'opt_metrics' in r else 0, # Fix safe access
            "Sentiment": r['sent_score'],
            "RSI": r['rsi'],
            "BTD": "✅" if r['btd'] else "❌",
            "MTF": "✅" if r['mtf'] else "❌",
            "Kevin Fund": f"{r['fundamental']['score']}/{r['fundamental']['max_score']}" if r['fundamental'] else "N/A"
        }
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # --- Tabs Layout ---
    tab1, tab2 = st.tabs(["📋 Scanner Table", "🃏 Detailed Cards"])
    
    with tab1:
        # Styled Table with Pandas Styler
        st.dataframe(
            df.style.background_gradient(subset=['Conviction'], cmap='RdYlGn', vmin=0, vmax=100)
                    .format(precision=2),
            column_config={
               "Conviction": None, # Hide raw
                "Conviction Label": st.column_config.TextColumn("Conviction"),
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )
        
    with tab2:
        for r in results:
            # Re-use existing card logic, adapted slightly
            with st.expander(f"**{r['ticker']}** - Conviction: {r['overall_score']} | Tech: {r['tech_score']}"):
                col1, col2, col3 = st.columns(3)
                
                # Technical Column
                with col1:
                    st.markdown("### 📊 Technical")
                    st.progress(r['tech_score']/100)
                    st.write(f"**Price Momentum:** {r['price_score']}/100")
                    st.write(f"**Volume/Flow:** {r['flow_score']}/100")
                    
                    st.markdown("#### 🎲 Options Data")
                    opt = r['opt_metrics']
                    st.write(f"**Options Score:** {r['opt_score']}/100")
                    st.caption(f"PCR (Vol): {opt.get('pcr_volume', 'N/A'):.2f}")
                    st.caption(f"IV Skew: {opt.get('iv_skew', 'N/A'):.2f}")
                    
                    if r['btd']:
                        st.success("🔥 Buy The Dip Detected!")
                    if r['mtf']:
                        st.info("✅ Multi-Timeframe Confirmed")
                
                # Fundamental Column
                with col2:
                    st.markdown("### 🧠 Fundamentals")
                    if r['fundamental']:
                        f = r['fundamental']
                        st.progress(f['score']/f['max_score'])
                        
                        # Mini grid for fundamentals
                        f_cols = st.columns(3)
                        
                        # Row 1
                        r_m = f['results']['margins']
                        color = "green" if r_m['pass'] == True else "orange" if r_m['pass'] == 'partial' else "red"
                        f_cols[0].markdown(f":{color}[Margins]")
                        f_cols[0].caption(r_m['msg'])
                        
                        r_g = f['results']['growth']
                        color = "green" if r_g['pass'] == True else "orange" if r_g['pass'] == 'partial' else "red"
                        f_cols[1].markdown(f":{color}[Growth]")
                        f_cols[1].caption(r_g['msg'])
                        
                        r_o = f['results']['oplev']
                        color = "green" if r_o['pass'] == True else "red"
                        f_cols[2].markdown(f":{color}[Op Lev]")
                        f_cols[2].caption(r_o['msg'])
                        
                        # Row 2
                        f_cols_2 = st.columns(3)
                        r_b = f['results']['balance']
                        color = "green" if r_b['pass'] == True else "orange" if r_b['pass'] == 'partial' else "red"
                        f_cols_2[0].markdown(f":{color}[Balance]")
                        f_cols_2[0].caption(r_b['msg'])
                        
                        r_v = f['results']['val']
                        color = "green" if r_v['pass'] == True else "orange" if r_v['pass'] == 'partial' else "red"
                        f_cols_2[1].markdown(f":{color}[Valuation]")
                        f_cols_2[1].caption(r_v['msg'])
                        
                        r_i = f['results']['insider']
                        color = "green" if r_i['pass'] == True else "orange" if r_i['pass'] == 'partial' else "red"
                        f_cols_2[2].markdown(f":{color}[Insiders]")
                        f_cols_2[2].caption(r_i['msg'])

                    else:
                        st.write("Fundamental scan skipped (Non-Equity).")

                # News Column (Moved to 3rd column)
                with col3:
                    st.markdown("### 📰 Sentiment")
                    st.write(f"**Sent Score:** {r['sent_score']}/100")
                    if r['news']:
                        for n in r['news']:
                            st.markdown(f"- [{n['title']}]({n['link']})")
                            st.caption(f"{n['pubDate']}")
                    else:
                        st.info("No recent news found.")
                        


if __name__ == "__main__":
    main()
