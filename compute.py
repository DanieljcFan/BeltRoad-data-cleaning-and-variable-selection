# -*- coding: utf-8 -*-
import ConfigParser

from django.db import connection
import pandas as pd

# 读取指定配置文件
cf = ConfigParser.ConfigParser()
cf.read("company_name.ini")
cf1 = ConfigParser.ConfigParser()
cf1.read("conf.ini")

# 对财务数据进行计算
class Calculation_Results:

    def __init__(self):
        pass

    def financial_report(self,name,year,column=None):
        '''
        营业收入 tr_sopl == revenue\
        营业成本 oc_sopl == cost   ->statement_of_profit_or_losst_merge_wind
        净利润   np_sopl == profit   /
        经营活动产生的现金流量净额 ncgf_socf == cash ->cash_flow_statement_merge_wind
        :param name: 需要统计数据的公司
        :param year: 需要统计的时间段
        :param column: 指定获取对应的财务数据，默认为取全部
        :return:
        '''
        # 将字符串截取成list
        try:
            name_list = name.split(",")
            year_list = year.split(",")
        except:
            name_list = [name]
            year_list = [year]
        result_list = []
        raw_result = []
        for y in year_list:
            for i in range(4):

                # 判断是否是第一季度数据 若是则保留元数据，如若不是则进行计算，公式：每季度所有公司各个数据之和-上一季度对应的数据
                if 1 == i+1:
                    # 创建数据库连接
                    cursor = connection.cursor()
                    place_holders = ','.join(map(lambda x: '%s', name_list))
                    sql = 'SELECT a.quarter,SUM(a.ncgf_socf),SUM(b.tr_sopl),SUM(b.oc_sopl),SUM(b.np_sopl) FROM cash_flow_statement_merge_wind_dev a,statement_of_profit_or_losst_merge_wind_dev b WHERE a.year=b.year AND a.year="'+y+'" AND a.quarter=b.quarter AND a.quarter="'+str(i+1)+'" AND a.corp_name IN (%s) AND a.corp_name = b.corp_name  AND a.report_period=b.report_period'
                    # 根据sql查询数据
                    cursor.execute(sql%place_holders,name_list)
                    raw = cursor.fetchall()

                    # 判断是否存在数据，如果没有跳过进行下一次循环
                    if None == raw[0][0]:
                        continue
                    raw_list = list(raw[0])
                    raw_result.append(raw[0])
                    result_list.append(raw_list)
                    raw_list[0] = y+" Q"+str(i+1)
                else:
                    # 创建数据库连接
                    cursor = connection.cursor()
                    place_holders = ','.join(map(lambda x: '%s', name_list))
                    sql = 'SELECT a.quarter,SUM(a.ncgf_socf),SUM(b.tr_sopl),SUM(b.oc_sopl),SUM(b.np_sopl) FROM cash_flow_statement_merge_wind_dev a,statement_of_profit_or_losst_merge_wind_dev b WHERE a.year=b.year AND a.year="' + y + '" AND a.quarter=b.quarter AND a.quarter="' + str(
                        i + 1) + '" AND a.corp_name IN (%s) AND a.corp_name = b.corp_name  AND a.report_period=b.report_period'

                    # 根据sql查询数据
                    cursor.execute(sql % place_holders, name_list)
                    raw = cursor.fetchall()

                    # 判断是否存在数据，如果没有跳过进行下一次循环
                    if None == raw[0][0]:
                        continue

                    # 当前季度数据减去对应的上一季度数据
                    raw_list = list(raw[0])
                    raw_list[1] = raw[0][1] - raw_result[i-1][1]
                    raw_list[2] = raw[0][2] - raw_result[i-1][2]
                    raw_list[3] = raw[0][3] - raw_result[i-1][3]
                    raw_list[4] = raw[0][4] - raw_result[i-1][4]
                    raw_list[0] = y + " Q" + str(i + 1)
                    result_list.append(raw_list)
                    raw_result.append(raw[0])

        # 将结果集转成数据框
        result_frame = pd.DataFrame(result_list,columns=["time","cash","revenue","cost","profit"])

        # 将数据框输出成csv
        result_frame.to_csv("financial_statistics.csv")
        if column is None:
            return result_frame
        else:
            result_frame = result_frame[["time",column]]
            return result_frame
