# -*- coding: utf-8 -*-
import sys

import numpy
import pandas as pd
import datetime
from industry.models import CoalIndustryD, CoalIndustryM, CoalIndustryS, CoalIndustryW, OilAndGasExploitationS, \
    OilAndGasExploitationD, OilAndGasExploitationM, OilAndGasExploitationW, PesticideIndustryS, PesticideIndustryY, \
    PesticideIndustryD, PesticideIndustryM, PetrochemicalEngineeringD, PetrochemicalEngineeringM, \
    PetrochemicalEngineeringW, PlasticIndustryD, PlasticIndustryM, PlasticIndustryW, RubberIndustryW, RubberIndustryM, \
    RubberIndustryD, SteelIndustryS, SteelIndustryY, SteelIndustryD, SteelIndustryM, SteelIndustryW, AluminiumIndustryS, \
    AluminiumIndustryD, AluminiumIndustryM, AluminiumIndustryW, CopperIndustryS, CopperIndustryY, CopperIndustryD, \
    CopperIndustryM, CopperIndustryW, GlassIndustryD, GlassIndustryM, PipeIndustryS, PipeIndustryD, PipeIndustryM, \
    PipeIndustryW, CementIndustryS, CementIndustryY, CementIndustryD, CementIndustryM, CementIndustryW, SteelStructureS, \
    SteelStructureD, SteelStructureM, DecorationS, DecorationD, DecorationM, DecorationW, MotorIndustryS, \
    MotorIndustryD, \
    MotorIndustryM, MotorIndustryW, EaAndHlW, EaAndHlM, EaAndHlD, EaAndHlQ, EngineeringMachineryQ, \
    EngineeringMachineryY, \
    EngineeringMachineryD, EngineeringMachineryM, EngineeringMachineryW, RailwayEquipmentQ, RailwayEquipmentD, \
    RailwayEquipmentM, RailwayEquipmentW, RefrigerationAirConditionerQ, RefrigerationAirConditionerD, \
    RefrigerationAirConditionerM, AutoPartsQ, AutoPartsD, AutoPartsM, AutoPartsW, CommercialTruckQ, CommercialTruckY, \
    CommercialTruckD, CommercialTruckM, WhiteHouseholdAppliancesQ, WhiteHouseholdAppliancesY, WhiteHouseholdAppliancesD, \
    WhiteHouseholdAppliancesM, WhiteHouseholdAppliancesW, AudiovisualsS, AudiovisualsD, AudiovisualsM, AudiovisualsW, \
    TextileGarmentQ, TextileGarmentD, TextileGarmentM, ClothingHomeTextileQ, ClothingHomeTextileD, ClothingHomeTextileM, \
    ClothingHomeTextileW, PackagePrintingS, PackagePrintingD, PackagePrintingM, PapermakingIndustryD, \
    PapermakingIndustryM, PapermakingIndustryW, GeneralRetailersM, GeneralRetailersS, LiquorIndustryS, LiquorIndustryD, \
    LiquorIndustryM, LiquorIndustryW, BeerIndustryS, BeerIndustryD, BeerIndustryM, BeerIndustryW, HotelIndustryS, \
    HotelIndustryD, HotelIndustryM, NaturalSightS, NaturalSightD, NaturalSightM, NaturalSightW, ThermalPowerIndustryS, \
    ThermalPowerIndustryD, ThermalPowerIndustryM, ThermalPowerIndustryW, HydropowerIndustryS, HydropowerIndustryD, \
    HydropowerIndustryM, WaterIndustryM, PortIndustryS, PortIndustryD, PortIndustryM, PortIndustryW, \
    RailwayTransportationQ, RailwayTransportationD, RailwayTransportationM, RailwayTransportationW, \
    RealEstateDevelopmentQ, RealEstateDevelopmentD, RealEstateDevelopmentM, RealEstateDevelopmentW, Matchup
from django.apps import apps

reload(sys)
sys.setdefaultencoding('utf-8')


class ScreenData:
    def __init__(self):
        pass

    def process(self, tableName,begintime,endtime):
        d1 = datetime.datetime(begintime, 1, 1)
        d2 = datetime.datetime(endtime, 03, 31)
        agDf = pd.DataFrame()
        nowDf = pd.DataFrame()
        screenData = ScreenData()
        table = screenData.processTable(tableName)
        for i in range(0, len(table["name"])):
            # 获取对象
            modelobj = apps.get_model('industry', table["name"][i])
            agList = []  # 累计值
            nowList = []  # 当前值
            # 循环对象那个的每一个属性
            for field in modelobj._meta.fields:
                name = field.name  # 获取对象属性名字
                if 'id' != name and 'create_time' != name and 'report_period' != name:  # 这几个字段不做处理
                    query = Matchup.objects.values('value_type').filter(column_name=field.name).filter(
                        table_name=tableName).using("industry")  # 查出字段是累计值还是当前值
                    entry = None
                    try:
                        entry = query[0]
                    except Exception,e:
                        print name,";;;;;;;;"
                        print tableName,";;;;;;"
                    valueType = entry.get('value_type')
                    if '1' == valueType:
                        agList.append(field.name)  # 累计值放在这里
                    else:
                        nowList.append(field.name)  # 当前值放在这里
            if 0 < len(agList):
                agList.append('report_period')  # 加入报告期字段
                defer = table["model"][i].objects.defer('id').defer('create_time').values(*agList).using("industry")  # 查询累计值字段
                # print str(table["model"][i].objects.defer('id').defer('create_time').values(*agList).filter(
                #     Q(report_period__contains="1111") | Q(report_period__contains="-06-30") | Q(
                #         report_period__contains="-09-30") | Q(report_period__contains="-12-31")).query)
                # 转换成dataframe
                if agDf.empty:
                    agDf = pd.DataFrame(list(defer))
                else:
                    agDf = pd.merge(agDf, pd.DataFrame(list(defer)))
            # 下面是当前值（同上）
            if 0 < len(nowList):
                nowList.append('report_period')
                defer = table["model"][i].objects.defer('id').defer('create_time').values(*nowList).using("industry")
                if nowDf.empty:
                    nowDf = pd.DataFrame(list(defer))
                else:
                    nowDf = pd.merge(nowDf, pd.DataFrame(list(defer)), how='outer')
        values = pd.DataFrame()
        datalist = pd.DataFrame()

        if not agDf.empty:
            agDf =agDf[~ agDf['report_period'].str.contains('-01-31')] #去掉一月份的值
            agDf['report_period'] = pd.to_datetime(agDf['report_period']) #转成日期格式
            agDf = agDf.set_index('report_period')  #设置日期索引
            agDf = agDf[agDf.index >= d1]  # 去掉指定日期的数据
            agDf = agDf[agDf.index <= d2]
            agDf = agDf.replace('nan', 0)
            agDf = agDf.astype('float')
            agDf4 = agDf.resample('Q').max().to_period('Q')  # 最大值

            # 计算累计值中每个季度的值
            for i in range(0, agDf4.iloc[:, 0].size):
                if 'Q1' in str(agDf4.iloc[i:i + 1].index) or 0 == i:
                    value3 = agDf4.iloc[i:i + 1]
                else:
                    value1 = agDf4.iloc[i - 1:i]
                    value2 = agDf4.iloc[i:i + 1]
                    value1.index = value2.index
                    value3 = value2 - value1
                if values.empty:
                    values = value3
                else:
                    values = values.append(value3)
            resultList = screenData.processBlank(values.index)  # 季度加空格
            values['report_period'] = resultList
        if not nowDf.empty:
            nowDf['report_period'] = pd.to_datetime(nowDf['report_period'])
            nowDf = nowDf.set_index('report_period')
            nowDf = nowDf[nowDf.index >= d1]
            nowDf = nowDf[nowDf.index <= d2]
            # print(nowDf.isnull().values.any())
            mow4 = nowDf.replace('nan', 0)
            mow4 = mow4.astype('float') #转换为数字格式 方便计算
            nowDf2 = mow4.resample('Q').sum().to_period('Q')  # 总数
            nowDf3 = nowDf.resample('Q').count().to_period('Q')  # 个数
            datalist = nowDf2 / nowDf3  # 均值
            resultList = screenData.processBlank(datalist.index)  # 季度加空格
            datalist['report_period'] = resultList

        #合并两个结果集
        datalist2 = pd.DataFrame()
        if not values.empty and not datalist.empty:
            datalist2 = pd.merge(datalist, values)
        elif values.empty:
            datalist2 = datalist
        elif datalist.empty:
            datalist2 = values

        if datalist2.empty:
            return None
        #把report_period放在第一列
        df_report_period = datalist2.report_period
        datalist2 = datalist2.drop('report_period', axis=1)
        datalist2.insert(0, 'time', df_report_period)
        datalist2[datalist2 == 0] = numpy.NaN
        datalist2 = datalist2.dropna(how='any',axis=1)
        return datalist2

    # 加空格
    def processBlank(self, dataList):
        resultList = []
        for data in dataList:
            resultList.append(str(data).replace("Q", " Q"))
        return resultList

    # 根据转进来的表名  分别查出实体类名
    def processTable(self, tableName):
        map = {}
        nameList = []
        modelList = []
        if "petrochemical_engineering" == tableName:
            nameList.append('PetrochemicalEngineeringD')
            nameList.append('PetrochemicalEngineeringM')
            nameList.append('PetrochemicalEngineeringW')
            modelList.append(PetrochemicalEngineeringD)
            modelList.append(PetrochemicalEngineeringM)
            modelList.append(PetrochemicalEngineeringW)
        elif 'pipe_industry' == tableName:
            nameList.append('PipeIndustryD')
            nameList.append('PipeIndustryM')
            nameList.append('PipeIndustryS')
            nameList.append('PipeIndustryW')
            modelList.append(PipeIndustryD)
            modelList.append(PipeIndustryM)
            modelList.append(PipeIndustryS)
            modelList.append(PipeIndustryW)
        elif 'plastic_industry' == tableName:
            nameList.append('PlasticIndustryD')
            nameList.append('PlasticIndustryM')
            nameList.append('PlasticIndustryW')
            modelList.append(PlasticIndustryD)
            modelList.append(PlasticIndustryM)
            modelList.append(PlasticIndustryW)
        elif 'port_industry' == tableName:
            nameList.append('PortIndustryD')
            nameList.append('PortIndustryM')
            nameList.append('PortIndustryS')
            nameList.append('PortIndustryW')
            modelList.append(PortIndustryD)
            modelList.append(PortIndustryM)
            modelList.append(PortIndustryS)
            modelList.append(PortIndustryW)
        elif 'railway_equipment' == tableName:
            nameList.append('RailwayEquipmentD')
            nameList.append('RailwayEquipmentM')
            nameList.append('RailwayEquipmentQ')
            nameList.append('RailwayEquipmentW')
            modelList.append(RailwayEquipmentD)
            modelList.append(RailwayEquipmentM)
            modelList.append(RailwayEquipmentQ)
            modelList.append(RailwayEquipmentW)
        elif 'railway_transportation' == tableName:
            nameList.append('RailwayTransportationD')
            nameList.append('RailwayTransportationM')
            nameList.append('RailwayTransportationQ')
            nameList.append('RailwayTransportationW')
            modelList.append(RailwayTransportationD)
            modelList.append(RailwayTransportationM)
            modelList.append(RailwayTransportationQ)
            modelList.append(RailwayTransportationW)
        elif 'real_estate_development' == tableName:
            nameList.append('RealEstateDevelopmentD')
            nameList.append('RealEstateDevelopmentM')
            nameList.append('RealEstateDevelopmentQ')
            nameList.append('RealEstateDevelopmentW')
            modelList.append(RealEstateDevelopmentD)
            modelList.append(RealEstateDevelopmentM)
            modelList.append(RealEstateDevelopmentQ)
            modelList.append(RealEstateDevelopmentW)
        elif 'refrigeration_air_conditioner' == tableName:
            nameList.append('RefrigerationAirConditionerD')
            nameList.append('RefrigerationAirConditionerM')
            nameList.append('RefrigerationAirConditionerQ')
            modelList.append(RefrigerationAirConditionerD)
            modelList.append(RefrigerationAirConditionerM)
            modelList.append(RefrigerationAirConditionerQ)
        elif 'rubber_industry' == tableName:
            nameList.append('RubberIndustryD')
            nameList.append('RubberIndustryM')
            nameList.append('RubberIndustryW')
            modelList.append(RubberIndustryD)
            modelList.append(RubberIndustryM)
            modelList.append(RubberIndustryW)
        elif 'refrigeration_air_conditioner' == tableName:
            nameList.append('RefrigerationAirConditionerD')
            nameList.append('RefrigerationAirConditionerM')
            nameList.append('RefrigerationAirConditionerQ')
            modelList.append(RefrigerationAirConditionerD)
            modelList.append(RefrigerationAirConditionerM)
            modelList.append(RefrigerationAirConditionerQ)
        elif 'steel_industry' == tableName:
            nameList.append('SteelIndustryD')
            nameList.append('SteelIndustryM')
            nameList.append('SteelIndustryS')
            nameList.append('SteelIndustryW')
            modelList.append(SteelIndustryD)
            modelList.append(SteelIndustryM)
            modelList.append(SteelIndustryS)
            modelList.append(SteelIndustryW)
        elif 'steel_structure' == tableName:
            nameList.append('SteelStructureD')
            nameList.append('SteelStructureM')
            nameList.append('SteelStructureS')
            modelList.append(SteelStructureD)
            modelList.append(SteelStructureM)
            modelList.append(SteelStructureS)
        elif 'textile_garment' == tableName:
            nameList.append('TextileGarmentD')
            nameList.append('TextileGarmentM')
            nameList.append('TextileGarmentQ')
            modelList.append(TextileGarmentD)
            modelList.append(TextileGarmentM)
            modelList.append(TextileGarmentQ)
        elif 'thermal_power_industry' == tableName:
            nameList.append('ThermalPowerIndustryD')
            nameList.append('ThermalPowerIndustryM')
            nameList.append('ThermalPowerIndustryS')
            nameList.append('ThermalPowerIndustryW')
            modelList.append(ThermalPowerIndustryD)
            modelList.append(ThermalPowerIndustryM)
            modelList.append(ThermalPowerIndustryS)
            modelList.append(ThermalPowerIndustryW)
        elif 'water_industry' == tableName:
            nameList.append('WaterIndustryM')
            modelList.append(WaterIndustryM)
        elif 'white_household_appliances' == tableName:
            nameList.append('WhiteHouseholdAppliancesD')
            nameList.append('WhiteHouseholdAppliancesM')
            nameList.append('WhiteHouseholdAppliancesQ')
            nameList.append('WhiteHouseholdAppliancesW')
            modelList.append(WhiteHouseholdAppliancesD)
            modelList.append(WhiteHouseholdAppliancesM)
            modelList.append(WhiteHouseholdAppliancesQ)
            modelList.append(WhiteHouseholdAppliancesW)
        elif 'aluminium_industry' == tableName:
            nameList.append('AluminiumIndustryD')
            nameList.append('AluminiumIndustryM')
            nameList.append('AluminiumIndustryS')
            nameList.append('AluminiumIndustryW')
            modelList.append(AluminiumIndustryD)
            modelList.append(AluminiumIndustryM)
            modelList.append(AluminiumIndustryS)
            modelList.append(AluminiumIndustryW)
        elif 'audiovisuals' == tableName:
            nameList.append('AudiovisualsD')
            nameList.append('AudiovisualsM')
            nameList.append('AudiovisualsS')
            nameList.append('AudiovisualsW')
            modelList.append(AudiovisualsD)
            modelList.append(AudiovisualsM)
            modelList.append(AudiovisualsS)
            modelList.append(AudiovisualsW)
        elif 'auto_parts' == tableName:
            nameList.append('AutoPartsD')
            nameList.append('AutoPartsM')
            nameList.append('AutoPartsQ')
            nameList.append('AutoPartsW')
            modelList.append(AutoPartsD)
            modelList.append(AutoPartsM)
            modelList.append(AutoPartsQ)
            modelList.append(AutoPartsW)
        elif 'beer_industry' == tableName:
            nameList.append('BeerIndustryD')
            nameList.append('BeerIndustryM')
            nameList.append('BeerIndustryS')
            nameList.append('BeerIndustryW')
            modelList.append(BeerIndustryD)
            modelList.append(BeerIndustryM)
            modelList.append(BeerIndustryS)
            modelList.append(BeerIndustryW)
        elif 'cement_industry' == tableName:
            nameList.append('CementIndustryD')
            nameList.append('CementIndustryM')
            nameList.append('CementIndustryS')
            nameList.append('CementIndustryW')
            modelList.append(CementIndustryD)
            modelList.append(CementIndustryM)
            modelList.append(CementIndustryS)
            modelList.append(CementIndustryW)
        elif 'clothing_home_textile' == tableName:
            nameList.append('ClothingHomeTextileD')
            nameList.append('ClothingHomeTextileM')
            nameList.append('ClothingHomeTextileQ')
            nameList.append('ClothingHomeTextileW')
            modelList.append(ClothingHomeTextileD)
            modelList.append(ClothingHomeTextileM)
            modelList.append(ClothingHomeTextileQ)
            modelList.append(ClothingHomeTextileW)
        elif 'coal_industry' == tableName:
            nameList.append('CoalIndustryD')
            nameList.append('CoalIndustryM')
            nameList.append('CoalIndustryS')
            nameList.append('CoalIndustryW')
            modelList.append(CoalIndustryD)
            modelList.append(CoalIndustryM)
            modelList.append(CoalIndustryS)
            modelList.append(CoalIndustryW)
        elif 'commercial_truck' == tableName:
            nameList.append('CommercialTruckD')
            nameList.append('CommercialTruckM')
            nameList.append('CommercialTruckQ')
            modelList.append(CommercialTruckD)
            modelList.append(CommercialTruckM)
            modelList.append(CommercialTruckQ)
        elif 'copper_industry' == tableName:
            nameList.append('CopperIndustryD')
            nameList.append('CopperIndustryM')
            nameList.append('CopperIndustryS')
            nameList.append('CopperIndustryW')
            modelList.append(CopperIndustryD)
            modelList.append(CopperIndustryM)
            modelList.append(CopperIndustryS)
            modelList.append(CopperIndustryW)
        elif 'decoration' == tableName:
            nameList.append('DecorationD')
            nameList.append('DecorationM')
            nameList.append('DecorationS')
            nameList.append('DecorationW')
            modelList.append(DecorationD)
            modelList.append(DecorationM)
            modelList.append(DecorationS)
            modelList.append(DecorationW)
        elif 'ea_and_hl' == tableName:
            nameList.append('EaAndHlD')
            nameList.append('EaAndHlM')
            nameList.append('EaAndHlQ')
            nameList.append('EaAndHlW')
            modelList.append(EaAndHlD)
            modelList.append(EaAndHlM)
            modelList.append(EaAndHlQ)
            modelList.append(EaAndHlW)
        elif 'engineering_machinery' == tableName:
            nameList.append('EngineeringMachineryD')
            nameList.append('EngineeringMachineryM')
            nameList.append('EngineeringMachineryQ')
            nameList.append('EngineeringMachineryW')
            modelList.append(EngineeringMachineryD)
            modelList.append(EngineeringMachineryM)
            modelList.append(EngineeringMachineryQ)
            modelList.append(EngineeringMachineryW)
        elif 'general_retailers' == tableName:
            nameList.append('GeneralRetailersM')
            nameList.append('GeneralRetailersS')
            modelList.append(GeneralRetailersM)
            modelList.append(GeneralRetailersS)
        elif 'glass_industry' == tableName:
            nameList.append('GlassIndustryD')
            nameList.append('GlassIndustryM')
            modelList.append(GlassIndustryD)
            modelList.append(GlassIndustryM)
        elif 'hotel_industry' == tableName:
            nameList.append('HotelIndustryD')
            nameList.append('HotelIndustryM')
            nameList.append('HotelIndustryS')
            modelList.append(HotelIndustryD)
            modelList.append(HotelIndustryM)
            modelList.append(HotelIndustryS)
        elif 'hydropower_industry' == tableName:
            nameList.append('HydropowerIndustryD')
            nameList.append('HydropowerIndustryM')
            nameList.append('HydropowerIndustryS')
            modelList.append(HydropowerIndustryD)
            modelList.append(HydropowerIndustryM)
            modelList.append(HydropowerIndustryS)
        elif 'liquor_industry' == tableName:
            nameList.append('LiquorIndustryD')
            nameList.append('LiquorIndustryM')
            nameList.append('LiquorIndustryS')
            nameList.append('LiquorIndustryW')
            modelList.append(LiquorIndustryD)
            modelList.append(LiquorIndustryM)
            modelList.append(LiquorIndustryS)
            modelList.append(LiquorIndustryW)
        elif 'motor_industry' == tableName:
            nameList.append('MotorIndustryD')
            nameList.append('MotorIndustryM')
            nameList.append('MotorIndustryS')
            nameList.append('MotorIndustryW')
            modelList.append(MotorIndustryD)
            modelList.append(MotorIndustryM)
            modelList.append(MotorIndustryS)
            modelList.append(MotorIndustryW)
        elif 'natural_sight' == tableName:
            nameList.append('NaturalSightD')
            nameList.append('NaturalSightM')
            nameList.append('NaturalSightS')
            nameList.append('NaturalSightW')
            modelList.append(NaturalSightD)
            modelList.append(NaturalSightM)
            modelList.append(NaturalSightS)
            modelList.append(NaturalSightW)
        elif 'oil_and_gas_exploitation' == tableName:
            nameList.append('OilAndGasExploitationD')
            nameList.append('OilAndGasExploitationM')
            nameList.append('OilAndGasExploitationS')
            nameList.append('OilAndGasExploitationW')
            modelList.append(OilAndGasExploitationD)
            modelList.append(OilAndGasExploitationM)
            modelList.append(OilAndGasExploitationS)
            modelList.append(OilAndGasExploitationW)
        elif 'package_printing' == tableName:
            nameList.append('PackagePrintingD')
            nameList.append('PackagePrintingM')
            nameList.append('PackagePrintingS')
            modelList.append(PackagePrintingD)
            modelList.append(PackagePrintingM)
            modelList.append(PackagePrintingS)
        elif 'papermaking_industry' == tableName:
            nameList.append('PapermakingIndustryD')
            nameList.append('PapermakingIndustryM')
            nameList.append('PapermakingIndustryW')
            modelList.append(PapermakingIndustryD)
            modelList.append(PapermakingIndustryM)
            modelList.append(PapermakingIndustryW)
        elif 'pesticide_industry' == tableName:
            nameList.append('PesticideIndustryD')
            nameList.append('PesticideIndustryM')
            nameList.append('PesticideIndustryS')
            modelList.append(PesticideIndustryD)
            modelList.append(PesticideIndustryM)
            modelList.append(PesticideIndustryS)
        map['name'] = nameList
        map['model'] = modelList
        return map
