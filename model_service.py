# -*- coding: utf-8 -*-
import ConfigParser
import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy import stats
from sklearn import linear_model
from sklearn import preprocessing
from sqlalchemy import create_engine

from industry.company.compute import Calculation_Results
from industry.company.screen_data import ScreenData
from industry.utils.transition import Utils

# 读取指定配置文件
cf = ConfigParser.ConfigParser()
cf.read("conf.ini")
cf2 = ConfigParser.ConfigParser()
cf2.read("company_name.ini")
class Model:
    def __init__(self):
        pass

    # 接受处理数据
    def data(self):

        '''当前方法主要功能为将处理后的行业数据与行业营收数据进行合并'''
        utils = Utils()
        calculation = Calculation_Results()
        screen = ScreenData()
        stair = cf.get("finance_time", "stair")
        second = cf.get("finance_time", "second")

        # 财务数据统计
        name = cf2.get(stair, second)
        year = cf.get("finance_time","year")
        compute = cf.get("finance_time", "compute")
        csv1_revenue = calculation.financial_report(name,year,compute)

        # 数据处理
        # 在此修改需要观看的行业对应的数据库表名 在time_config.ini文件中标有对应关系
        begintime = int(cf.get("time", "start_time"))
        endtime = int(cf.get("time", "end_time"))
        tableName = cf.get("industry","industry_name")
        csv1_car = screen.process(tableName,begintime,endtime)
        if csv1_car is None:
            print "没有数据"
            return "没有数据"
        num = csv1_car.columns.size
        if num == 1:
            print "数据nan"
            return "数据nan"
        csv1_car  = csv1_car.reset_index(drop = True)
        # 获取每列数据标题（字段名）将行业营收数据标题与行业数据标题合并（从行业数据第二列开始获取标题，去除与行业营收数据重复标题）
        csv1_revenue_columns = csv1_revenue.columns.values.tolist()
        csv1_car_columns = csv1_car.ix[:, 1:].columns.values.tolist()
        columns_name = csv1_revenue_columns + csv1_car_columns
        date = csv1_car[["time"]]
        date_dummies = utils.season_dummy(date)

        # 原始数据添加季节因子虚拟变量
        original_data = csv1_car.join(date_dummies.ix[:, 0:])

        # 遍历出与行业营收数据的时间对应的行业数据
        list = []
        csv1_revenue_list = np.array(csv1_revenue).tolist()
        for i in csv1_revenue_list:

            # 查找与行业营收数据的时间对应的行业数据
            csv1_car_index = csv1_car[(csv1_car.time == i[0])]

            # 将dataframe转变成list
            index_list = np.array(csv1_car_index.ix[:, 1:]).tolist()
            if len(index_list) == 0:
                continue
            list_result = i + index_list[0]
            list.append(list_result)

        # 将对应后的数据转换成DataFrame，columns_name是列名
        result_df = pd.DataFrame(list, columns=columns_name)

        # 提取时间列
        result_time = result_df[["time"]]

        # 将季节因子转换成虚拟变量
        dummies = utils.season_dummy(result_time)
        season_list = utils.season_list(result_time)
        result_df_copy = result_df.iloc[:, 0:]

        # 将季节虚拟变量合并到数据中
        result_df = result_df.join(dummies.ix[:, 1:])
        del result_df_copy["time"]
        result_df_copy["season"] = season_list
        del result_df_copy[compute]
        contrast = result_df["time"]
        del result_df["time"]
        y = result_df[compute]
        del result_df[compute]
        # del result_df["ppi_production_process_dolomite"]
        # del result_df_copy["ppi_production_process_dolomite"]
        # 在此调用筛选模型matching 按住ctrl键与鼠标左键点击，可跳转到相应的方法
        model = self.matching(y, result_df, result_df_copy)

        # 打开文件流 用于输出信息到 *.txt文件
        f = open('model.txt', 'w')

        # 获取当前时间
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print >> f, "时间:", now_time
        index_id = model[0]
        x_result = result_df.iloc[:, index_id]
        x_z = np.array(x_result, dtype=np.float)
        y_y = np.array(y, dtype=np.float)
        x_h = sm.add_constant(result_df.iloc[:, index_id])
        x_h = x_h.astype(float)
        y_h = y.astype(float)

        # 对回归模型进行综合展示，展示公式形式，进入模型的变量及其系数，及其他评测模型的因素，最主要用的是Multiple R-squared
        clf = linear_model.LinearRegression()

        # lm1 = smf.OLS(y_h, x_h).fit()
        #
        # # 残差均值，数值越小意味着预测误差会越小，主要用于主观评定
        # clf.fit(x_z, y_y)
        # pred = clf.predict(x_z)
        # resid_list = []
        #
        # # 计算残差（y-predict）
        # for i in range(len(pred)):
        #     difference = y_y[i] - pred[i]
        #     resid_list.append(difference)
        # resid_list = np.array(resid_list, dtype=np.float)
        # resid_mean = np.mean(abs(resid_list / y))
        # print >> f, "残差均值:", resid_mean
        #
        # # 方差膨胀因子，用于主观评测
        # vif_list = []
        # for j in index_id:
        #     y_g = result_df.iloc[:, j]
        #     index_result_remove = index_id[:]
        #
        #     # 移除指定数据
        #     index_result_remove.remove(j)
        #     X = result_df.iloc[:, index_result_remove]
        #
        #     # 建立模型
        #     clf.fit(X, y_g)
        #
        #     # 求r2
        #     square = clf.score(X, y_g)
        #     vf = 1 / (1 - square)
        #     vif_list.append(vf)
        # vif_list = self.list_to_numberic(vif_list)
        # print >> f, "方差膨胀因子", vif_list
        # print >> f, utils.LINE
        # print >> f, "回归结果(A)"
        # print >> f, lm1.summary()

        # 手动筛选变量，去掉现有模型中的变量，这是主观部分****
        # index_id.pop(4)
        # index_id.pop(2)
        x_n = np.array(result_df.iloc[:, index_id], dtype=np.float)
        x_k = sm.add_constant(result_df.iloc[:, index_id])
        x_k = x_k.astype(float)
        y_k = y.astype(float)
        # 在去掉变量后重新回归，模型为lm1
        lm1 = smf.OLS(y_k, x_k).fit()
        test_time = "2018 Q1"
        data = original_data[original_data["time"] == test_time]
        if 0 == len(data):
            return ""
        # 删除指定字段
        del data["time"]
        del data["season_1"]

        # 截取数据框指定的列
        data = data.iloc[:, index_id]
        print >> f, utils.LINE
        print >> f, "回归结果(B)"
        print >> f, lm1.summary()

        # 模型预测结果
        clf.fit(x_n, y)
        pdt_model = clf.predict(x_n)

        # 利用模型lm1预测下一期的情况
        clf.fit(x_n, y)
        print >> f, utils.LINE
        print >> f, "回归模型截距（intercept）:", clf.intercept_

        # 建立模型
        pdt_data = clf.predict(data)

        # 将指定数据转换成数据框
        contrast = pd.DataFrame(contrast)
        contrast["actual"] = y
        contrast["pred"] = pdt_model

        # 将数据框转换成list
        contrast_nd = np.array(contrast).tolist()
        title = ["report_period","average_value","pre_value"]
        print >> f, "置信区间:"
        print >> f, "fit ", " lwr ", " upr "
        y = pd.DataFrame(y.tolist())
        x_n = pd.DataFrame(x_n.tolist())
        y_array = np.mat(y)
        x_array = np.mat(x_n)
        sigma2 = y_array.T * (np.eye(len(y_array), len(y_array)) - x_array * (x_array.T * x_array).I * x_array.T) * y_array / (x_n.iloc[:,0].size - x_n.columns.size - 1)

        # 循环预测值，并求出相应的置信区间
        for i in pdt_data:
            data = np.array(pd.DataFrame(data))
            distance = np.sqrt(1 + data * (x_array.T * x_array).I * data.T)
            se_y = np.sqrt(sigma2) * distance
            # 获取置信区间
            conf_int = stats.norm.interval(0.05, loc=pdt_data, scale = se_y) #variance undefined???
            row = []
            row.append(test_time)
            row.append("")
            row.append(i)
            contrast_nd.append(row)
            print >> f, i, "|", conf_int[0], "|", conf_int[1]
            pdf = pd.DataFrame({"report_period": "2018-03-31", "95_start": conf_int[0][0][0],
                                "95_end":conf_int[1][0][0],"fit":"","industry":cf.get("data","indus"),
                                "index_value":cf.get("data","index_value"),"pre_value":i}, index=[0])
            self.dataframe_insert(pdf,"industry_forecasts")
            print >> f, "sigma", np.sqrt(sigma2)
            print >> f, "distance:", distance
        # 关闭文件流
        f.close()
        contrast_result = pd.DataFrame(contrast_nd, columns=title)

        contrast_result["industry"] = cf.get("data","indus")
        contrast_result["index_value"] = cf.get("data","index_value")
        time_list = np.array(contrast_result["report_period"])
        date_list = []
        for i in time_list:
            i_arr = i.split(" ")
            if "Q1" == i_arr[1]:
                time_str = i_arr[0]+"-03-31"
            elif "Q4" == i_arr[1]:
                time_str = i_arr[0] + "-12-31"
            elif "Q2" == i_arr[1]:
                time_str = i_arr[0] + "-06-30"
            elif "Q3" == i_arr[1]:
                time_str = i_arr[0] + "-09-30"
            date_list.append(time_str)
        del contrast_result["report_period"]
        contrast_result["report_period"] = date_list
        # self.dataframe_insert(contrast_result,"industry_average")
        contrast_result.to_csv("contrast_result.csv", index=False, sep=',')
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》"
        # 从数据框中取出指定列的值
        # actual = np.array(contrast_result["actual"]).tolist()
        # actual1 = np.array(contrast_result["actual"]).tolist()
        # actual1 = actual1[0:len(actual1)-1]
        # num = len(actual)
        # if actual[num-1] == 0:
        #     actual[num-1] = None
        # pred = np.array(contrast_result["pred"]).tolist()
        # time_x = np.array(contrast_result["time"]).tolist()
        # x_time = []
        #
        # # 去除季节因子中的'Q'
        # for i in time_x:
        #     season_x = i.split('Q')
        #     time_str = season_x[0] + season_x[1]
        #     x_time.append(time_str)
        #
        # # 添加画图数据，plt.plot(x,y)
        # plt.plot(x_time, pred, 'r',label='pred')
        # plt.plot(x_time, actual, 'b',label='actual')
        # plt.title('model')
        # plt.xlabel('time')
        # plt.ylabel('value')
        #
        # # 显示label
        # plt.legend()
        # plt.grid()
        #
        # # 通过该命令启动服务器查看图形 python manage.py runserver --nothreading --noreload
        # plt.savefig('contrast.jpg', format='jpg')
        # plt.show()
        #
        # pred = pred[0:len(pred)-1]

        # 残差散点图
        # plt.scatter(pred, preprocessing.scale(np.array(actual1) - np.array(pred)))
        # plt.xlabel('predict')
        # plt.ylabel('residual')
        # plt.savefig('residual.jpg', format='jpg')
        # plt.show()

    def list_to_numberic(self, list_old, digit=2):
        list_new = []
        for list_str in list_old:
            if list_str == None:
                list_new.append(0)
            else:
                list_new.append(round(list_str,digit))
        return list_new


    # 对数据进行拟合建模
    def matching(self, y, x, x_copy, must=None, vif=5, method="aic"):

        '''
        当前方法将根据行业营收数据与行业数据进行建模
        :param y:因变量
        :param x:可用自变量 season为虚拟变量
        :param x_copy 可用自变量 season为数值
        :param must:必须保留在模型中的变量所在的列号（注意此时是去除因变量后的列号）默认为空
        :param vif:方差膨胀因子的阈值，默认为5
        :return (list): index最终模型自变量X的列数(list),x_result
        '''
        utils = Utils()
        # r2为空列，用来存储单因子预测时的拟合效果
        r2 = pd.DataFrame()

        # 将列标题转换成数字，利于遍历
        X_list = np.array(x_copy).tolist()
        count = len(X_list[0])
        list1 = []
        index_count = 0
        for i in range(count):
            list1.append(str(i))
            index_count += 1
        df = pd.DataFrame(X_list, columns=list1)
        num = 0
        clf = linear_model.LinearRegression()

        # 计算因变量的方差,从自变量的第一列到最后一列做for循环
        for i in range(count):
            # 只用第i列与因变量做拟合
            X = df[[str(i)]]
            clf.fit(X, y)
            r_square = clf.score(X, y)

            # 求得单变量预测模型的r2
            pdf = pd.DataFrame({"r2": r_square, "id": num}, index=["0"])
            r2 = r2.append(pdf, ignore_index=True)
            num += 1

        # 指定index为进入模型的列号，首先添加must
        # 如果指定列index有值，求出r2值
        index = [must]
        r2_0 = None
        aic0 = None
        if index[0] is not None:
            X = x.iloc[:, index]
            clf.fit(X, y)
            r2_0 = clf.score(X, y)
            residual = clf.predict(X) - y
            aic0 = 2*X.shape[1] + X.shape[0] * np.log(sum(residual*residual)/X.shape[0])

        # 按r2将所有列从大到小排序，依次进入for循环
        r2 = r2.sort_values(ascending=False, by="r2")
        id = np.array(r2["id"]).tolist()
        count_id = len(id) - 1
        for i in id:
            vif_list = []
            if index[0] is None:
                if i == count_id:
                    index[0] = count_id
                    index.append(count_id + 1)
                    index.append(count_id + 2)
                else:
                    index[0] = i
            if i in index:
                continue
            index_result = index[:]

            # 判断如果是季节因子字段，就将其合并成一组数据进行处理
            if i == count_id:
                index_result.append(count_id)
                index_result.append(count_id + 1)
                index_result.append(count_id + 2)
            else:
                index_result.append(i)
            X = x.iloc[:, index_result]
            clf.fit(X, y)

            # 计算当前模型的方差膨胀因子
            for j in index_result:

                if j == count_id + 2 or j == count_id + 1:
                    continue

                # 再次判断如果是季节因子字段 就通过下面的方法求vif
                if j == count_id:

                    # 因季节因子为虚拟变量，所以将三列值合并成一组数据
                    j = [j]
                    j.append(count_id + 1)
                    j.append(count_id + 2)
                    index_result_remove = index_result[:]
                    index_result_remove.remove(count_id)
                    index_result_remove.remove(count_id + 1)
                    index_result_remove.remove(count_id + 2)
                    y_b = x.iloc[:, j]
                    x_a = x.iloc[:, index_result_remove]
                    # 调用frame方法 求vif
                    v = utils.frame(y_b,x_a)
                    vif_list.append(v)
                    continue
                else:
                    index_result_remove = index_result[:]
                    index_result_remove.remove(j)
                    y_b = x.iloc[:, j]
                    x_a = x.iloc[:, index_result_remove]
                clf.fit(x_a, y_b)
                square = clf.score(x_a, y_b)
                if square == 1:
                    vif_list.append(0)
                    continue
                v = 1 / (1 - square)
                vif_list.append(v)

            # # 如果新的模型vif的最大值超过了阈值，则说明该变量带来强多重共线性，抛弃该变量进入下一次循环
            if max(vif_list) > vif:
                continue

            # 计算调整后的r2
            clf.fit(X, y)
            a = clf.score(X, y)
            num = len(index_result) + 1
            r2_1 = 1 - (1 - a) * (15 - 1) / (15 - num)
            residual = clf.predict(X) - y
            aic1 = 2 * X.shape[1] + X.shape[0] * np.log(sum(residual * residual) / X.shape[0])

            if "aic" == method:
                if aic0 == None:
                    index = index_result[:]
                    aic0 = aic1
                elif aic1 < aic0:
                    index = index_result[:]
                    aic0 = aic1
            elif "r2" == method:
                # 如果新模型的r2大于原模型的r2，则需要将该变量接纳进模型
                if r2_1 > r2_0:
                    index = index_result[:]
                    r2_0 = r2_1
            else:
                return None
        return [index]

    def dataframe_insert(self, frame, table_name, echo=False):
        '''
               第一个参数thedataframe是需要导入的pd dataframe,
               第二个参数tablename是将导入的数据库中的表名
               第三个参数engine是启动数据库的接口，pd 1.9以后的版本，除了sqllite，均需要通过sqlalchemy来设置
               第四个参数databasename是将导入的数据库名字
               第五个参数if_exists='append'的意思是，如果表tablename存在，则将数据添加到这个表的后面
               :param param:
               :return:
               '''
        db_info = {'user': 'root',
                   'password': 'root',
                   'host': '10.0.0.103',
                   'database': 'test'  # 这里我们事先指定了数据库，后续操作只需要表即可
                   }
        engine = create_engine('mysql://%(user)s:%(password)s@%(host)s/%(database)s?charset=utf8' % db_info,
                               encoding='utf-8', echo=echo)
        frame.to_sql(table_name, engine, if_exists='append')
# SSR = sum(residual * residual)
# AIC = 2*p + n*np.log(SSR/n)