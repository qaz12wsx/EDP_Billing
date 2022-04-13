from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import datetime
from bs4 import BeautifulSoup


# 將值轉為數字
def stringToInt(string):
    if string.index("$") != 0:
        num = string[2:]
        return float(num.replace(',', ''))*-1
    else:
        num = string[1:]
    return float(num.replace(',', ''))
    
# Switch Role 可能出現的頁面
def CfmRolePage():
    try:
        driver.find_element(by=By.ID, value='switchrole_firstrun_button')
        return True
    except:
        return False

# AWS 自動登出後
def sessiontimeout():
    try:
        driver.find_element(by=By.LINK_TEXT, value="here")
        driver.get("https://10.2.1.62/adfs/ls/IdpInitiatedSignOn.aspx")
        driver.find_element(by=By.ID, value='idp_SignInToOtherRpPanel').click()
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'nav-usernameMenu')))
        driver.get("https://console.aws.amazon.com/billing/home?region=us-east-2#/bills")
        # Switch Role
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'nav-usernameMenu')))
        driver.find_element(by=By.ID, value="nav-usernameMenu").click()
        driver.find_element(by=By.LINK_TEXT, value="Switch role").click()
        return True
    except:
        return True

options=webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
driver = webdriver.Chrome(options=options, service=Service(r"C:\Users\emily.huang\Downloads\chromedriver"))

driver.get("https://10.2.1.62/adfs/ls/IdpInitiatedSignOn.aspx")

message = ""
while message != "yes":
    message = input("登入完成後請輸入 'yes'")
    
print("登入完成 ")

# 進入 Billing 頁面
driver.get("https://console.aws.amazon.com/billing/home?region=us-east-2#/bills")

while True:
# Switch Role
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'nav-usernameMenu')))
    driver.find_element(by=By.ID, value="nav-usernameMenu").click()
    driver.find_element(by=By.LINK_TEXT, value="Switch role").click()
    
    switchpage = sessiontimeout()
    switchpage = CfmRolePage()
    
    if switchpage:
        driver.find_element(by=By.ID, value='switchrole_firstrun_button').click()
    
    
    # 輸入 Account
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'account')))
    
    account = ""
    while account == "":
        account = input("請輸入account：")
    
    driver.find_element(by=By.ID, value="account").send_keys(account)
    driver.find_element(by=By.ID, value="roleName").send_keys("ADFS-BillingAccess")
    driver.find_element(by=By.ID, value="input_switchrole_button").click()
    
    # 獲取當前時間，取得上個月的內容
    today = datetime.datetime.today()
    year = str(today.year)
    month = int(today.month) - 1
    driver.get("https://us-east-1.console.aws.amazon.com/billing/home?region=us-east-2#/bills?year="+year+"&month="+str(month))
    
    
    # 抓取資料
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    total = driver.find_element(by=By.CLASS_NAME, value="currency.total-amount").text
    total = stringToInt(total)
    marketSec = driver.find_elements(by=By.ID, value="marketPlaces")
    
    if len(marketSec) != 1:
        market = marketSec[0].find_element(by=By.CLASS_NAME, value="ng-binding").text
        market = stringToInt(market)
        serviceUsage = marketSec[1].find_element(by=By.CLASS_NAME, value="ng-binding").text
        serviceUsage = stringToInt(serviceUsage)
    else:
        market = 0
        serviceUsage = marketSec[0].find_element(by=By.CLASS_NAME, value="ng-binding").text
        serviceUsage = stringToInt(serviceUsage)
    
    creditSec = soup.find("span", attrs={"data-testid":"credits-text"})
    if creditSec != "None":
        credit = creditSec.getText()
        credit = credit[credit.index("$"):] #擷取 $ 後的字串
        credit = credit[:credit.index(" ")] #擷取空白前的字串
        credit = stringToInt(credit)
    else:
        credit = 0
    
    creditMemoSec = soup.find('div', attrs={"data-testid": "discounts-section"})
    if creditMemoSec != "None":
        creditMemo = creditMemoSec.find("span", attrs={"class":"ng-binding"}).getText()
        creditMemo = creditMemo[creditMemo.index("$"):] #擷取 $ 後的字串
        creditMemo = creditMemo[:creditMemo.index(" ")] #擷取空白前的字串
        creditMemo = stringToInt(creditMemo)
    else:
        creditMemo = 0
    
    CDNSec = soup.find("awsui-expandable-section", attrs={"header":"CloudFront "})
    if CDNSec != "None":
        CDNAfter = CDNSec.find_previous_sibling("span").getText()
        CDNAfter = stringToInt(CDNAfter)
        # CDNDiscount = CDNSec.find("div", attrs={"class":"edp-discounts-information"}).find('span', attrs={'class':"awsui-util-f-r"}).getText()
        # CDNDiscount = stringToInt(CDNDiscount)
    else:
        CDNAfter = 0
        # CDNDiscount = 0
    
    shieldSec = soup.find("awsui-expandable-section", attrs={"header":"Shield "})
    if shieldSec != "None":
        shield = shieldSec.find_previous_sibling("span").getText()
        shield = stringToInt(shield)
    else:
        shield = 0
        
    ESSec = soup.find("awsui-expandable-section", attrs={"header":"Premium Support "})
    if ESSec != "None":
        ES = ESSec.find_previous_sibling("span").getText()
        ES = stringToInt(ES)
    else:
        ES = 0
    usageBeforeEDP = serviceUsage + creditMemo + credit - ES
    DataList = [shield, CDNAfter, credit, usageBeforeEDP, creditMemo, serviceUsage, market, ES, total]
    print(total, market, serviceUsage, credit, creditMemo, CDNAfter, shield, ES, usageBeforeEDP)
    print(DataList)
