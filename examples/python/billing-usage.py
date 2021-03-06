#! /usr/bin/python
""" Sample client for billing-usage.

This client pulls the reportSources you have access to.
For the first result, it pulls all products.  Then it
creates monthly reports for the range you specify for
each product, and finally creates a CSV for the whole
range.  

The combination of calls should be sufficient to let
you do what you need with the billing-usage API.

Contact open-developer@akamai.com with questions, ideas
or comments.

Thanks!
"""

import requests, logging, json
from random import randint
from akamai.edgegrid import EdgeGridAuth
from config import EdgeGridConfig
from urlparse import urljoin
import urllib
session = requests.Session()
debug = False

config = EdgeGridConfig({},"billingusage")

# Enable debugging for the requests module
if debug:
  import httplib as http_client
  http_client.HTTPConnection.debuglevel = 1
  logging.basicConfig()
  logging.getLogger().setLevel(logging.DEBUG)
  requests_log = logging.getLogger("requests.packages.urllib3")
  requests_log.setLevel(logging.DEBUG)
  requests_log.propagate = True


# Set the config options
session.auth = EdgeGridAuth(
            client_token=config.client_token,
            client_secret=config.client_secret,
            access_token=config.access_token
)

if hasattr(config, 'headers'):
	session.headers.update(config.headers)

baseurl = '%s://%s/' % ('https', config.host)

def getResult(endpoint, parameters=None):
	if parameters:
		parameter_string = urllib.urlencode(parameters)
		path = ''.join([endpoint + '?',parameter_string])
	else:
		path = endpoint
	endpoint_result = session.get(urljoin(baseurl,path))
	if debug: print ">>>\n" + json.dumps(endpoint_result.json(), indent=2) + "\n<<<\n"
	return endpoint_result.json()

def getFileResult(endpoint, parameters=None):
	if parameters:
		parameter_string = urllib.urlencode(parameters)
		path = ''.join([endpoint + '?',parameter_string])
	else:
		path = endpoint
	endpoint_result = session.get(urljoin(baseurl,path))
	return endpoint_result

def getReportSources():
	print
	print "Requesting the list of report sources"

	events_result = getResult('/billing-usage/v1/reseller/reportSources')
	return events_result['contents']

def getProducts(parameter_obj,startdate,enddate):
	print
	print "Requesting a list of products for the given time period"
	headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Accept':'application/json'}
        path = "/billing-usage/v1/products"

	parameters = {	"reportSources"	:parameter_obj,
			"startDate"	:startdate,
			"endDate"	:enddate
		}
	data_string = urllib.urlencode({p: json.dumps(parameters[p]) for p in parameters})
	products_result = session.post(urljoin(baseurl,path),data=data_string, headers=headers)
	products_obj = json.loads(products_result.text)
	return products_obj['contents']

def getCsvReport(product_list, startdate, enddate, source_obj):
        print
        print "Requesting a csv report for the given time period"
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        path = "/billing-usage/v1/contractUsageData/csv"

        parameters = {  "reportSources" :[source_obj],
			"products"	:product_list,
                        "startDate"     :startdate,
                        "endDate"       :enddate
                }
        print
        data_string = urllib.urlencode({p: json.dumps(parameters[p]) for p in parameters})
        products_result = session.post(urljoin(baseurl,path),data=data_string, headers=headers)
        products_csv = products_result.text
        return products_csv

def getMeasures(product, startdate, enddate, source_obj):
	print
	print "Requesting the list of measures valid for product %s" % product
	parameters = {	'startMonth':startdate['month'],
			'endMonth':enddate['month'],
			'startYear':startdate['year'],
			'endYear':enddate['year'],
			'reportSourceId':source_obj['id'],
			'reportSourceType':source_obj['type'],
			'productId':product
			}
	path_string = '/'.join(['/billing-usage/v1/measures', product, source_obj['type'], source_obj['id'], startdate['month'], startdate['year'], enddate['month'], enddate['year']])
	measures_result = getResult(path_string)

def getStatisticTypes(product, startdate, enddate, source_obj):
	print
	print "Requesting the list of statistic types valid for product %s" % product
	parameters = {	'startMonth':startdate['month'],
			'endMonth':enddate['month'],
			'startYear':startdate['year'],
			'endYear':enddate['year'],
			'reportSourceId':source_obj['id'],
			'reportSourceType':source_obj['type'],
			'productId':product
			}
	path_string = '/'.join(['/billing-usage/v1/statisticTypes', product, source_obj['type'], source_obj['id'], startdate['month'], startdate['year'], enddate['month'], enddate['year']])
	statistics_result = getResult(path_string)
	return statistics_result['contents']

def getMonthlyReport(product, startdate, statistictype, source_obj):
	print
	path_string = '/'.join(['/billing-usage/v1/contractUsageData/monthly', product, source_obj['type'], source_obj['id'], statistictype, startdate['month'], startdate['year'],startdate['month'], startdate['year']])
	report_result = getResult(path_string)

if __name__ == "__main__":
	# getReportSources will return a list of reporting groups and/or contract ids
	# include the group or contract as contractId and the reportType as returned
	# by getReportSources
	# You could loop through them here, or just get one big kahuna report and chunk it up yourself
	reportSource = getReportSources()
	contractId = reportSource[0]['id']
	reportType = reportSource[0]['type']
	measures = {}
	statisticTypes = {}

	# Now, for a list of the products available for the reporting dates for these reporting sources

	source_obj = {
                "id" : contractId,
                "type" : reportType
        }

	startdate = {
		"month":"9", 
		"year":"2014"
	}
	
	enddate = {
		"month":"9",
		"year":"2014"
	}

	products = getProducts(source_obj, startdate, enddate)
	product_list = []
	for product in products:
		product_list.append({"id":product['id']})
		measures[product['id']] = getMeasures(product['id'], startdate, enddate, source_obj)
		statisticTypes = getStatisticTypes(product['id'], startdate, enddate, source_obj)
		for statisticType in statisticTypes:
			getMonthlyReport(product['id'],startdate,statisticType['statisticType'],source_obj)
		
	"""
	Get a CSV report for all products here, using the information we gathered above
	"""
	report = getCsvReport(product_list, startdate, enddate, source_obj)
	print report


