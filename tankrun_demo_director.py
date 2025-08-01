"""
这是 Left 4 Dead 2 插件企划 "下一代 Tank Run 优化方案" 对应的 demo. 本 demo 用于辅助理解该方案所需变量, 函数, 类和算法的实现, 无法被游戏程序直接调用.
本 demo 包含生成坦克的自定义 "导演系统" 的相关功能模块, 其他模块请详见对应后缀名的 demo 文件.

企划设计: 大藏游星
企划审查: 智无知, 白尾
"""

# --------------------------------------------------------------------------------------------------------------------------------------------------- #

import math
import random

""" --- 自定义 "导演系统" 所需全局变量 --- """

# 插件执行频率, 0.1代表每0.1秒执行一次插件的主程序
directorExecutionFrequency = 0.1

# 坦克数量的上限, 默认值为22 (对应的所有包括死亡和旁观的生还者数量为8), 最小值为16 (对应的所有包括死亡和旁观的生还者数量为14)
# 如果当前生还者总数超过8人, 则会另外施加随着人数的增加而呈 "指数级增长" 的负面效果
# 如果当前生还者总数超过14人, 则会强制结束游戏 (炸服)
# 不开放修改权限
tankLimit = 22

# 坦克待生成队列; 在没有对等待生成的坦克添加额外信息的情况下, 可以视为一个整数, 初始值为0
idleTankNum = 0

# 坦克生成目标频率, 5.0代表每5.0秒向坦克待生成队列添加坦克, 允许的取值为 2.0 - 8.0
# 后续可开放修改权限, 默认值为5.0, 输入格式只能保留一位小数点, 否则无视输入
goalFrequency = 5.0

# 坦克生成时间间隔的标准左区间, 初始值为0.0
# 不开放修改权限, 出于取值会被动态修改的考虑
standardLeftInterval = 0.0

# 坦克生成时间间隔的标准右区间, 初始值为 2 * goalFrequency
# 不开放修改权限, 出于取值会被动态修改的考虑
standardRightInterval = 2.0 * goalFrequency

# 生还者组别的标准压力阈值, 允许的取值为 200 - 1100
# 后续可开放修改权限, 默认值为600, 输入格式只能为整数, 否则无视输入
standardStressValue = 600



# --- 记录所需客户端数据 --- #

# 存储 当前 所有生还者客户端 (不 包括死亡和旁观生还者)
satisfiedSurvivorClients = []

# 记录 当前 生还者客户端数量 (包括死亡和旁观生还者)
survivorClientNum = 0

# 存储 当前 所有坦克客户端
tankClients = []

# 记录 当前 坦克客户端数量
tankClientNum = 0

# 存储 当前 所有生还者实例化类
survivorClassList = []

# 存储 当前 所有坦克实例化类
tankClassList = []

# 存储 上一次插件执行周期中 所有生还者实例化类, 用于生还者类信息在不同执行周期中的传递
last_survivorClassList = []

# 存储 上一次插件执行周期中 所有坦克实例化类, 用于坦克类信息在不同执行周期中的传递
last_tankClassList = []

# 存储 当前 所有生还者组别实例化类
survivorGroupClassList = []

# 存储 上一次插件执行周期中 所有生还者组别实例化类, 用于生还者组别类信息在不同执行周期中的传递
last_survivorGroupClassList = []



# --- dirEucD函数视为0欧式位移的上下界 --- #

# 视为0欧式位移的导演距离上界
dirEucNoMovementUpBoundary = +110.0

# 视为0欧式位移的导演距离下界
dirEucNoMovementDownBoundary = -110.0



# --- 用于检查生还者短时行动切片的变量 --- #

# 切换至冲刺切片的边界
rushSliceBoundary = +300.0

# 切换至后退切片的边界
backSliceBoundary = -300.0

# 切换至防守切片的上下界
defendSliceUpBoundary = +150.0
defendSliceDownBoundary = -150.0



# --- 生还者切换至 S Status 所需满足的与终点安全区域的导演距离边界 --- #
flowDistanceToFinalCheckPoint = 1000.0




""" --- 获取所需要的客户端 --- """

def getSatisfiedClientFromGame():  
    """
    获取并返回所有满足条件的客户端列表和各自的数量
    """
    # 存储生还者客户端 (不 包括死亡和旁观生还者)
    satisfiedSurvivorClients = []   

    # 存储坦克客户端
    tankClients = []

    # 记录生还者客户端数量 (包括死亡和旁观生还者)
    survivorClientNum = 0

    # 记录坦克客户端数量
    tankClientNum = 0

    for client in Game.getAllClients():  # 假设游戏获取所有客户端的函数为getAllClients
        
        if client.type() == Survivor:   # 假设获取客户端类型的函数为type
            
            survivorClientNum += 1

            if (not client.isDead()) and (not client.isAway()):   # 获取所有 非 死亡和旁观的生还者
                
                satisfiedSurvivorClients.append(client)

        elif client.type() == Tank:   # 获取所有在场的坦克
            
            tankClientNum += 1
            tankClients.append(client)
    
    return satisfiedSurvivorClients, survivorClientNum, tankClients, tankClientNum




""" --- 自定义 "导演系统" 所需函数和算法 --- """

def euclideanDistance(pos1: tuple, pos2: tuple):    # 计算欧式距离, 输入数据为两个三元组坐标
    eD = math.sqrt(
        (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + (pos1[2] - pos2[2]) ** 2
    )

    return eD




""" 后续需要修改 """
# def maxDistance( mainTarget: Client, deputyTarget: Client ):     # 假设生还者和坦克均继承自Client类, mainTarget和deputyTarget的类型可以为生还者或坦克
#     """
#     获取mainTarget和deputyTarget的maxD距离, 其中mainTarget是主要目标 (为mainTarget计算maxD距离), deputyTarget是副目标
#     """
#     return max(
#         euclideanDistance( mainTarget.getAbsolutePosition(), deputyTarget.getAbsolutePosition() ),
#         abs( mainTarget.getFlowDistance() - deputyTarget.getFlowDistance() )
#     )




def stressComputeModel_RG( D: float ):
    """
    冲刺型生还者组别逻辑压力计算函数
    """
    if 0 <= D <= 2100:
        return 100.0 * (2100.0 - D) / 2100.0    # 保证返回的数值为浮点型
    
    elif D < 0:
        return 100.0    # 异常值处理
    
    else:
        return 0.0


def stressComputeModel_DG( D: float ):
    """
    防守型生还者组别逻辑压力计算函数
    """
    if 0 <= D <= 1050:
        return 100.0
    
    elif 1050 < D <= 3150:
        return 100.0 * (3150.0 - D) / 2100.0
    
    elif D < 0:
        return 100.0
    
    else:
        return 0.0


def stressComputeModel_BG( D: float ):
    """
    后退型生还者组别逻辑压力计算函数
    """
    if 0 <= D <= 3150:
        return 100.0 * (3150.0 - D) / 3150.0
    
    elif D < 0:
        return 100.0
    
    else:
        return 0.0


# --- 以下函数搭建生还者和生还者组别之间的桥梁 --- #

def getSurvivorClassListSortedByFlowDist(satisfiedSurvivorClients: list, last_survivorClassList: list):
    """
    实例化所有满足条件的生还者客户端为生还者类, 并按照导演路程的先后顺序排序
    注意, 对于已经被实例化的生还者客户端, 不需要再次实例化, 而是更新其对应实例化类的信息
    而对于上一次插件执行流程存在, 此次流程不存在的生还者客户端, 其对应的实例化类会被自动舍弃
    
    parameters:
    @satisfiedSurvivorClients: 从游戏中获取的 生还者客户端 列表
    @last_survivorClassList: 上一个插件执行周期中的 生还者实例化类 列表

    return:
    @survivorClassList: 当前的 生还者实例化类 列表
    """
    if len(satisfiedSurvivorClients) <= 0:      # 没有存活的生还者, 异常值处理, 注意不可以使用 survivorClientNum <= 0 进行判断
        return []    # 实例化生还者类失败
    
    survivorClassList = []
    

    # --- 创建新的survivorClassList --- #

    # 请确保 satisfiedSurvivorClients 和 last_survivorClassList 添加的数据都是生还者客户端
    
    if len(last_survivorClassList) > 0:     # 过去存在生还者实例化类, 说明插件已经不是第一次执行

        for surClient in satisfiedSurvivorClients:
            
            findClassFlag = False   # 生还者客户端是否找到了自己的实例化类

            for surClass in last_survivorClassList:

                if surClient.getIdentification() == surClass.survivorID:         # 假设获取客户端唯一标识的方法为getIdentification, 不可使用steamID, 出于对闲置的考虑
                    
                    surClass.updateSurvivorInfo(surClient)      # 更新对应实例化类的数据
                    survivorClassList.append(surClass)      # 存入更新后的生还者实例化类

                    findClassFlag = True        # 生还者客户端找到了自己的实例化类
                    break       # 结束查找
                
            if not findClassFlag:       # 如果生还者客户端没有找到自己的实例化类, 说明其有可能刚刚复活 / 加入游戏, 为其创建实例化类
                
                surClass = SurvivorClass(surClient)
                survivorClassList.append(surClass)      # 存入新创建的生还者实例化类

    else:       # 过去不存在生还者实例化类, 说明插件是第一次执行
        
        for surClient in satisfiedSurvivorClients:

            surClass = SurvivorClass(surClient)
            survivorClassList.append(surClass)


    # --- 为刚刚创建的survivorClassList排序 --- #

    # 自行实现按照实例化类的属性进行排序的算法, 因为不确定插件的ArrayList类是否自带类似的功能; 如果有, 下面的内容可以忽略
    # 冒泡排序, 按导演路程 降序 排序, 即靠前的生还者实例化类排在前面

    num = len(survivorClassList)

    for i in range( 0, num ):       # 左闭右开区间
        
        for j in range( 0, num - i - 1 ):
            
            if survivorClassList[ j ].flowDistance < survivorClassList[ j + 1 ].flowDistance:   # 将导演路程数值较小的实例化类逐步向列表末尾移动
                
                temp = survivorClassList[j]     # 临时变量
                survivorClassList[j] = survivorClassList[j + 1]
                survivorClassList[j + 1] = temp

    return survivorClassList    # 返回已经经过了排序的生还者实例化类队列



def survivorGroupingStrategy(survivorClassList: list):
    """
    通过分组策略为生还者实例化类队列分组, 并为每一个组别创建对应的生还者组别实例化类, 同时按照创建的顺序加入数组中
    组别实例化类在数组中的先后顺序 等价于 组别在 导演路程 中的先后顺序

    parameters:
    @survivorClassList: 已经经过处理的 生还者实例化类 列表

    return:
    @survivorGroupClassList: 当前的 组别实例化类 列表
    """
    pass



def getTankClassList(tankClients: list, last_tankClassList: list):
    """
    实例化所有的坦克客户端为坦克类
    注意, 对于已经被实例化的坦克客户端, 不需要再次实例化, 而是更新其对应实例化类的信息
    而对于上一次插件执行流程存在, 此次流程不存在的坦克客户端, 其对应的实例化类会被自动舍弃
    
    parameters:
    @tankClients: 从游戏中获取的 坦克客户端 列表
    @last_tankClassList: 上一个插件执行周期中的 坦克实例化类 列表

    return:
    @tankClassList: 当前的 坦克实例化类 列表
    """
    if len(tankClients) <= 0:      # 当前没有存活的坦克
        return []
    
    tankClassList = []


    # --- 创建新的tankClassList --- #

    # 请确保 tankClients 和 last_tankClassList 添加的数据都是坦克客户端
    
    if len(last_tankClassList) > 0:     # 过去存在坦克实例化类

        for tkClient in tankClients:
            
            findClassFlag = False   # 坦克客户端是否找到了自己的实例化类

            for tkClass in last_tankClassList:

                if tkClient.getIdentification() == tkClass.tankID:         # 假设获取客户端唯一标识的方法为getIdentification
                    
                    tkClass.updateTankInfo(tkClient)      # 更新对应实例化类的数据
                    tankClassList.append(tkClass)      # 存入更新后的坦克实例化类

                    findClassFlag = True        # 坦克客户端找到了自己的实例化类
                    break       # 结束查找
                
            if not findClassFlag:       # 如果坦克客户端没有找到自己的实例化类, 为其创建实例化类
                
                tkClass = TankClass(tkClient)
                tankClassList.append(tkClass)      # 存入新创建的坦克实例化类

    else:       # 过去不存在坦克实例化类
        
        for tkClient in tankClients:

            tkClass = TankClass(tkClient)
            tankClassList.append(tkClass)

    return tankClassList    # 返回坦克实例化类队列



def computeCurrSurvivorStress(survivorClassList: list, tankClassList: list, stressComputeModelType: str):
    pass




""" --- 自定义 "导演系统" 所需类的定义 --- """

class FixedSizeArray:
    """
    自定义先进先出的数组类型, Python中可以直接使用collections.deque实现该功能, 但不确定插件是否自带类似的数据结构; 如果有, 这部分的内容可以忽略
    """
    def __init__(self, maxSize):
        self.maxSize = maxSize
        
        if maxSize <= 0:
            raise ValueError("maxSize must be positive !")      # 直接停止插件的执行
        
        self.data = []

    def add_tuple_data(self, value: tuple):    # 存储的元素为二元组类型, 同时包含 (绝对坐标, 导演路程) 两个变量        
        if len(self.data) >= self.maxSize:
            
            # 移除最早加入的元素 (即索引 0 的元素)
            self.data.pop(0)
        
        self.data.append(value)

    def add_str_data(self, value: str):     # 存储的元素为字符串类型
        if len(self.data) >= self.maxSize:
            
            # 移除最早加入的元素 (即索引 0 的元素)
            self.data.pop(0)
        
        self.data.append(value)

    def get_all(self):
        return self.data.copy()     # 深度复制data, 避免修改同一内存

    def __len__(self):
        return len(self.data)   # 返回数组当前的长度
    


class SurvivorClass:
    """
    为每个生还者 Client 实例化一个生还者类
    """
    def __init__(self, client: Client):    # 假设游戏存储客户端所有信息的对象为Client类
        if client.type() != Survivor:
            raise ValueError("client is not Survivor type !")       # 直接停止插件的执行
        
        self.survivor = client

        self.survivorID = client.getIdentification()        # 假设获取客户端唯一标识的方法为getIdentification, 不可使用steamID, 出于对闲置的考虑

        self.instantCreateTime = Game.Time()    # 该实例化类创建的时间, 假设游戏获取当前时间的函数为Time


        # --- 从游戏中获取的数据 -- #

        # 假设获取客户端绝对坐标的函数为getAbsolutePosition, 数据类型为 (x, y, z) 三元组
        self.absolutePosition = self.survivor.getAbsolutePosition()   

        # 假设获取客户端导演路程的函数为getFlowDistance, 数据类型为浮点型
        self.flowDistance = self.survivor.getFlowDistance() 

        # 生还者当前是否倒地或者挂边, 假设获取生还者客户端是否倒地或挂边的函数分别为 isIncapacitied 和 isHangingLedge
        self.isIncapacitied = self.survivor.isIncapacitied() or self.survivor.isHangingLedge()


        # --- 自定义 "导演系统" 额外添加的数据 --- #

        # 该生还者当前是否应该被标记为S, 初始化为False
        # should_be_marked_as_S_Status可以被生还者自身, 或者被生还者组别切换至True; 但只能被生还者组别切换回False
        self.should_be_marked_as_S_Status = False
        
        # 生还者行动切片, 初始化为R (Slice)
        self.slice = "R"

        # 生还者所处状态, 初始化为R (Status)
        self.status = "R"

        # 长度为2秒的滑动窗口, 由于directorExecutionFrequency = 0.1, 因此实际长度为20
        # 该滑动窗口初始填充当前的 (绝对坐标, 导演路程) 数据, 长度为 1
        self.slice_2_sec_window = FixedSizeArray( int(2 / directorExecutionFrequency) )

        self.slice_2_sec_window.add_tuple_data( ( self.absolutePosition, self.flowDistance ) )

        # 长度为10秒的滑动窗口, 由于directorExecutionFrequency = 0.1, 因此实际长度为100
        # 该滑动窗口初始全部填充 R Slice
        self.status_10_sec_window = FixedSizeArray( int(10 / directorExecutionFrequency) )

        while len(self.status_10_sec_window.data) < self.status_10_sec_window.maxSize:
            self.status_10_sec_window.add_str_data( "R" )

        # 该生还者当前的压力值, 初始化为0, 生还者类内部无法更改该变量, 需要外部进行更改
        self.currSurvivorStress = 0

        # 该生还者所属的生还者组别的逻辑, 初始化为字符串 R, 生还者类内部无法更改该变量, 需要外部进行更改
        self.belongSurvivorGroupLogic = "R"

    
    def check_whether_in_S_Status(self):   # 生还者是否处于S Status, 已经集成了切换至S Status的逻辑
        """
        生还者可自行切换至S Status所需的条件, 该函数只允许被生还者类自身调用:
        1. 生还者进入了终点安全区域, 假设游戏判断生还者是否进入终点安全区域的函数为 isInFinalCheckPoint
        2. 生还者 未 倒地或者挂边
        3. 生还者与地图末尾的导演距离差距小于flowDistanceToFinalCheckPoint, 假设游戏获取地图完整导演路程的函数为getTotalFlowDistance
        4. 当前存活生还者大于1人, 注意不可以使用 survivorClientNum > 1 进行判断, 这是因为survivorClientNum记录了死亡和旁观的玩家
        """
        if self.survivor.isInFinalCheckPoint() and ( not self.isIncapacitied ) and abs( Game.getTotalFlowDistance() 
            - self.flowDistance ) < flowDistanceToFinalCheckPoint and len(satisfiedSurvivorClients) > 1:

            self.should_be_marked_as_S_Status = True

        return self.should_be_marked_as_S_Status
    

    def check_S_Status_by_external(self, value: bool):
        """
        外部检查生还者的S Status, 传入布尔值, 该函数生还者类自身不调用
        """
        self.should_be_marked_as_S_Status = value
        return self.should_be_marked_as_S_Status


    def is_slice_window_full(self):     # 判断slice滑动窗口是否填充完毕
        return len(self.slice_2_sec_window.data) >= self.slice_2_sec_window.maxSize


    def dirEucD(self):      # 计算dirEucD距离
        if not self.is_slice_window_full():     # 如果游戏刚开始, 或者生还者刚复活, 即slice滑动窗口没有填充完毕
            return 0

        # 请确保 slice_2_sec_window 添加的数据均为 (绝对坐标, 导演路程) 二元组
        # 过去2秒移动的导演路程大于dirEucNoMovementUpBoundary
        if ( self.slice_2_sec_window[ self.slice_2_sec_window.maxSize - 1 ][1]
             - self.slice_2_sec_window[ 0 ][1] ) > dirEucNoMovementUpBoundary:      
            
            return +euclideanDistance( self.slice_2_sec_window[ self.slice_2_sec_window.maxSize - 1 ][0], 
                                      self.slice_2_sec_window[ 0 ][0] )
            
        # 过去2秒移动的导演路程小于dirEucNoMovementUpBoundary
        if ( self.slice_2_sec_window[ self.slice_2_sec_window.maxSize - 1 ][1]
             - self.slice_2_sec_window[ 0 ][1] ) < dirEucNoMovementDownBoundary:
            
            return -euclideanDistance( self.slice_2_sec_window[ self.slice_2_sec_window.maxSize - 1 ][0], 
                                      self.slice_2_sec_window[ 0 ][0] )
        
        # 不满足上述所有条件, 则视为0位移
        else:
            return 0


    def check_slice(self):      # 检查生还者短时行动切片
        if self.slice not in ["R", "D", "B"]:   # 异常值处理
            self.slice = "R"

        if not self.is_slice_window_full():  # 如果游戏刚开始, 或者生还者刚复活, 即slice滑动窗口没有填充完毕
            pass    # 维持初始值R

        else:
            if self.dirEucD() > rushSliceBoundary and self.slice != "R":  # 过去2秒移动的dirEucD距离大于rushSliceBoundary
                self.slice = "R"    # 切换至 R Slice

            elif defendSliceDownBoundary <= self.dirEucD() <= defendSliceUpBoundary and self.slice != "D":    # 过去2秒移动的dirEucD距离位于 [defendSliceDownBoundary, defendSliceUpBoundary]
                self.slice = "D"    # 切换至 D Slice

            elif self.dirEucD() < backSliceBoundary and self.slice != "B":  # 过去2秒移动的dirEucD距离小于backSliceBoundary
                self.slice = "B"    # 切换至 B Slice

            else:
                pass    # 不满足上述任一判断条件, 则维持当前取值

        return self.slice   # 返回更新后的当前slice取值
    

    def check_status(self):     # 检查生还者当前状态
        if self.status not in ["R", "D", "B", "S", "I"]:    # 异常值处理
            self.status = "R"

        if self.isIncapacitied:     # I状态标记具有最高优先级
            self.status = "I"
        
        elif self.should_be_marked_as_S_Status:     # S状态标记具有第二高优先级 
            self.status = "S"
            
        else:   # 注意该滑动窗口初始化时已经全部填充 R Slice, 所以不会出现异常
            
            RSliceNum = 0
            DSliceNum = 0
            BSliceNum = 0
            RSliceNumAtTail = 0
            # DSliceNumAtTail = 0
            BSliceNumAtTail = 0

            # 请确保 status_10_sec_window 添加的数据均为 R, D, B 字符串
            for i in range( 0, self.status_10_sec_window.maxSize ):     # range为左闭右开区间
                
                if self.status_10_sec_window.data[ i ] == "R":
                    RSliceNum += 1
                    if i >= 0.6 * self.status_10_sec_window.maxSize:     # 处于末尾的R Slice
                        RSliceNumAtTail += 1

                elif self.status_10_sec_window.data[ i ] == "D":
                    DSliceNum += 1

                elif self.status_10_sec_window.data[ i ] == "B":
                    BSliceNum += 1
                    if i >= 0.6 * self.status_10_sec_window.maxSize:
                        BSliceNumAtTail += 1    # 处于末尾的B Slice

            # Status 标记的优先级 R > B > D
            
            if RSliceNum >= 0.6 * self.status_10_sec_window.maxSize or RSliceNumAtTail >= 30:     # R_Slice的数量 >= 60 或 末尾40个Slice中至少出现30个R_Slice
                self.status = "R"
            
            elif BSliceNum >= 0.6 * self.status_10_sec_window.maxSize or BSliceNumAtTail >= 30:     # B_Slice的数量 >= 60 或 末尾40个Slice中至少出现30个B_Slice
                self.status = "B"

            # elif DSliceNum >= 0.6 * self.status_10_sec_window.maxSize:    # D_Slice的数量 大于等于 60
            #     self.status = "D"

            else:       # 上述条件都不满足的情况下, 切换至D Status
                self.status = "D"

        return self.status      # 返回更新后的当前status取值


    # --- 下面的函数用于更新实例化类的信息 --- #

    def updateSurvivorInfo(self, client: Client):
        """
        注意事项:
        1. 传入的 client 的 ID 必须与该实例化生还者类的 survivorID 相同
        2. 不对刚完成实例化的生还者类调用此方法, 因为实例化过程已经更新了所有数据
        """
        if self.survivorID != client.getIdentification():   # survivor ID 不一致
            return False        # 不 停止插件的执行, 但处理不当将造成意想不到的错误
        
        if Game.Time() - self.instantCreateTime < directorExecutionFrequency:   # 不更新刚完成实例化的类的数据, 插件执行一次的时间通常不会超过0.1秒
            return False
        
        self.survivor = client  # 已知为生还者类型且survivorID, 因此部分数据无需重新更新


        # --- 只要该生还者 非 死亡和旁观, 那么以下信息将随着插件执行的频率更新 --- #
        
        # 假设获取客户端绝对坐标的函数为getAbsolutePosition, 数据类型为 (x, y, z) 三元组
        self.absolutePosition = self.survivor.getAbsolutePosition()   

        # 假设获取客户端导演路程的函数为getFlowDistance, 数据类型为浮点型
        self.flowDistance = self.survivor.getFlowDistance() 

        # 生还者当前是否倒地或者挂边, 假设获取生还者客户端是否倒地或挂边的函数分别为 isIncapacitied 和 isHangingLedge
        self.isIncapacitied = self.survivor.isIncapacitied() or self.survivor.isHangingLedge()
        
        # 自我更新should_be_marked_as_S_Status变量值
        self.check_whether_in_S_Status()    


        # --- 检查生还者状态的流程 --- #

        # 1. 根据新的绝对坐标和导演路程更新slice_2_sec_window
        self.slice_2_sec_window.add_tuple_data( ( self.absolutePosition, self.flowDistance ) )

        # 2. 根据新的slice_2_sec_window更新slice
        self.check_slice()

        # 3. 根据新的slice更新status_10_sec_window (简化操作, 无需像文档所提及的那样在前10秒采用覆盖的更新形式)
        self.status_10_sec_window.add_str_data( self.slice )

        # 4. 根据新的status_10_sec_window更新status, 其中I和S标记具有更高的优先级
        self.check_status()

        # --- 生还者内部无法计算压力值, 因此不更新currSurvivorStress --- #
        # --- 生还者内部无法判断所属组别的逻辑, 因此不更新belongSurvivorGroupLogic --- #

        return True     # 成功更新实例化生还者类信息



class TankClass:
    """
    为每个坦克 Client 实例化一个坦克类
    """
    def __init__(self, client: Client):    # 假设游戏存储客户端所有信息的对象为Client类
        if client.type() != Tank:
            raise ValueError("client is not Tank type !")       # 直接停止插件的执行
        
        self.tank = client

        self.tankID = client.getIdentification()        # 假设获取客户端唯一标识的方法为getIdentification, 不可使用steamID

        self.instantCreateTime = Game.Time()    # 该实例化类创建的时间, 假设游戏获取当前时间的函数为Time


        # --- 从游戏中获取的数据 -- #

        # 假设获取客户端绝对坐标的函数为getAbsolutePosition, 数据类型为 (x, y, z) 三元组
        self.absolutePosition = self.tank.getAbsolutePosition()   

        # 假设获取客户端导演路程的函数为getFlowDistance, 数据类型为浮点型
        self.flowDistance = self.tank.getFlowDistance()

        # 假设获取坦克仇恨目标的函数为 getFocusedTarget, 数据类型为Client (或非Client)
        self.focusedTarget = self.tank.getFocusedTarget()


        # --- 自定义 "导演系统" 额外添加的数据 --- #
        # ......


    def returnFocusedTarget(self):
        """
        被外部调用, 用于计算压力值等流程
        """
        return self.focusedTarget


    # --- 下面的函数用于更新实例化类的信息 --- #

    def updateTankInfo(self, client: Client):
        """
        注意事项:
        1. 传入的 client 的 ID 必须与该实例化坦克类的 tankID 相同
        2. 不对刚完成实例化的坦克类调用此方法, 因为实例化过程已经更新了所有数据
        """
        if self.tankID != client.getIdentification():   # tank ID 不一致
            return False        # 不 停止插件的执行, 但处理不当将造成意想不到的错误
        
        if Game.Time() - self.instantCreateTime < directorExecutionFrequency:   # 不更新刚完成实例化的类的数据, 插件执行一次的时间通常不会超过0.1秒
            return False
        
        self.tank = client  # 已知为坦克类型且tankID, 因此部分数据无需重新更新


        # --- 只要该坦克 非 死亡, 那么以下信息将随着插件执行的频率更新 --- #
        
        # 假设获取客户端绝对坐标的函数为getAbsolutePosition, 数据类型为 (x, y, z) 三元组
        self.absolutePosition = self.tank.getAbsolutePosition()   

        # 假设获取客户端导演路程的函数为getFlowDistance, 数据类型为浮点型
        self.flowDistance = self.tank.getFlowDistance()

        # 假设获取坦克仇恨目标的函数为 getFocusedTarget, 数据类型 **未知**
        self.focusedTarget = self.tank.getFocusedTarget()

        return True     # 成功更新实例化坦克类信息



class SurvivorGroupClass:
    """
    为每个生还者组别 Survivor Group 实例化一个组别类
                                                                *** 非常复杂, 请仔细阅读注释 ***
    """
    def __init__(self, survivorClassListGroupingByStrategy: list):
        """
        parameters:
        @survivorClassListGroupingByStrategy: 被分组策略划分出来的 生还者实例化类 子列表
        """
        
        # 该组别中的所有生还者类成员
        self.survivorMembers = survivorClassListGroupingByStrategy

        # 生还者组别的的唯一标识, 由 survivorMembers 中的首位生还者的survivorID决定, 该ID将用于组别的合并与拆分, 以及数据的继承和复制
        # 详见 "方案" 第 3.1.3 小节: 生还者组别合并和拆分时数据的合并和复制
        self.survivorGroupID = survivorClassListGroupingByStrategy[ 0 ].survivorID

        # 成员的总数量
        self.memberNum = len(survivorClassListGroupingByStrategy)

        # 非 处于 I 状态的 成员数量
        self.notIMemberNum = 0

        for surClass in survivorClassListGroupingByStrategy:
            
            if surClass.status != "I":
                self.notIMemberNum += 1

        # 生还者组别 当前 所处的逻辑, 数据类型为字符串; 初始化为 R, 等待检查; 将会与生还者类的 belongSurvivorGroupLogic 一起检查
        # 只要得知了该生还者组别类的成员构成, 就能够从 内部 调用相应的函数判断 survivorGroupLogic 的取值
        self.survivorGroupLogic = "R"

        # 生还者组别 当前 的代表压力值, 数据类型为浮点型; 初始化为0, 等待检查; 将会与生还者类的 currSurvivorStress 一起计算; 
        # 只有得知了 所有 生还者组别类的成员构成, 以及 组别类的逻辑 以后, 才能够从 外部 调用相应的函数计算 survivorGroupStress 和 currSurvivorStress 的取值
        # 详见 “方案” 第 1.1.8 小节: gamma值的稀释
        self.survivorGroupStress = 0

        # 该生还者 组别 当前是否应该被标记为S逻辑, 初始化为False
        self.should_be_marked_as_S_Logic = False


        # --- 请求式申请生成坦克所需要的数据 --- #

        # 该组别生成坦克的时间间隔的 左区间, 默认为 标准左生成间隔取值
        self.leftSpawnInterval = standardLeftInterval

        # 该组别生成坦克的时间间隔的 右区间, 默认为 标准右生成间隔取值
        self.rightSpawnInterval = standardRightInterval

        # 该组别 下一次 生成坦克的时间间隔, 注意 左右区间 会被压力动态调控策略更改, 因此需要定义方便外部更改 左右区间 取值的接口, 初始值随机生成
        self.spawnInterval = random.uniform( self.leftSpawnInterval, self.rightSpawnInterval )      # 包含两端, 生成随机浮点数; 不需要截断小数位, 因为插件的执行频率已经决定了生成坦克间隔的精度

        # 该组别 上一次 生成坦克的游戏时间, 初始值为 该生还者组别实例化类 被创建的时间
        # 对于游戏刚开始第一个坦克延迟刷新的现象 ( 因为组别类被实例化时的spawnInterval不为0 ), 可以在插件的主循环中添加额外的判断条件强制刷新第一个坦克 (可以不解决)
        # 组别类被实例化时的spawnInterval 不宜 设置为0, 考虑到较大的起始点区域可能会使插件开始执行时同时创建多个组别, 此时spawnInterval初始化为0会导致插件在游戏开始后
        # 非常短的时间内就尝试向后方组别附近生成坦克
        self.lastSpawnTime = Game.Time()

        # 是否开始请求在组别附近生成坦克, 初始化为False
        self.whetherRequestTank = False


        # --- 检查并更新初始化的信息 --- #

        # 检查 should_be_marked_as_S_Logic 的取值
        self.check_whether_in_S_Logic()     
        
        # 检查 survivorGroupLogic 的取值
        self.check_logic()      



    def check_whether_in_S_Logic(self):        # 生还者组别是否处于S Logic, 已经同时集成了 进入 和 退出 S Logic 的逻辑
        """
        检查生还者组别是否应该 进入 还是 退出 S Logic;
        生还者组别进入 S Logic, 那么生还者组别中 所有的 成员类都应该进入 S Status; 反之, 如果生还者组别退出 S Logic, 那么生还者组别中 所有的 成员类都应该退出 S Status;
        因此, 这一流程需要调用生还者类中的 check_S_Status_by_external 函数 ( 在后续的 check_logic 函数中 )

        进入 S Logic 需要满足如下条件:
            存在标记为 S Status, 且当前 导演路程 与 终点区域 的距离小于 flowDistanceToFinalCheckPoint 的生还者
        退出 S Logic 需要满足如下条件:
            全员倒地;
            或 出现了除I Status和S Status以外的生还者, 且 不 存在与终点区域距离小于 flowDistanceToFinalCheckPoint 的S Status生还者
        不满足上述任何条件, 则维持当前的取值不变

        设计的理由:
            如果前方的生还者已经抵达安全区域, 就不向在该区域的生还者附近生成坦克, 以减少有限的坦克 Client 数量的浪费;
            进入了 S Status 的生还者无法自行退出此状态, 以防止生还者刻意离开安全区域帮助后方生还者分散坦克的生成位置;
            只有当前方生还者主动离开安全区域并加入 仍然远离安全区域 的后方生还者, 才重新使该前方生还者退出 S Status, 方便在其附近生成坦克
        """
        
        if self.notIMemberNum == 0:     # 全员倒地或者挂边
            
            self.should_be_marked_as_S_Logic = False    # 不应该被标记为 S Logic
            return self.should_be_marked_as_S_Logic     # 返回False
        
        else:         # 组别中存在正常生还者

            existStatusExceptSandI = False     # 是否出现存在除了S和I Status以外的生还者

            for surClass in self.survivorMembers:

                if surClass.status != "I" and surClass.status != "S":   # 同时不处于I和S状态
                    existStatusExceptSandI = True

                elif surClass.status == "S":    # 存在标记为 S Status 的生还者

                    if abs( Game.getTotalFlowDistance() - surClass.flowDistance ) < flowDistanceToFinalCheckPoint:  # 且当前导演路程与终点区域的距离小于flowDistanceToFinalCheckPoint
                        
                        self.should_be_marked_as_S_Logic = True
                        return self.should_be_marked_as_S_Logic     # 结束搜索, 返回True

            if existStatusExceptSandI == True:      # 出现了除I Status和S Status以外的生还者, 且已知不存在与终点区域距离小于flowDistanceToFinalCheckPoint的S生还者
                self.should_be_marked_as_S_Logic = False

            # 若不满足上述所有条件, 则维持当前取值不变

        return self.should_be_marked_as_S_Logic     # 返回 (更新后的) should_be_marked_as_S_Logic 取值



    def check_logic(self):
        """
        只要得知了该生还者组别类的成员构成, 就可以从组别类内部调用, 检查 survivorGroupLogic 属性
        同时, 也会修改所有属于该组别的成员的 belongSurvivorGroupLogic 属性
        除此之外, 还需要调用生还者类中的 check_S_Status_by_external 函数以确保同组别中生还者的 S状态取值 统一性
        """
        if self.survivorGroupLogic not in ["R", "D", "B", "S", "I"]:    # 异常值处理
            self.survivorGroupLogic = "R"

        
        # --- 根据该生还者组别类的 should_be_marked_as_S_Logic 检查与更新 生还者组别类 的Logic 和 生还者成员类 的Status --- #
        
        if self.should_be_marked_as_S_Logic:    # 满足进入S Logic的所有条件时; 注意should_be_marked_as_S_Logic的判断条件自带"不能全员倒地"
            
            self.survivorGroupLogic = "S"       # 组别被标记为 S

            # --- 覆盖组别内生还者的Status的取值 --- #

            # 即便survivorGroupLogic的取值早已为S, 也需要 重复 对生还者进行检查, 避免 生还者自行变更其 status 的取值 
            # 我知道你们会吐槽代码中存在很多重复操作, 由于这是我第一次自行设计逻辑如此复杂的功能, 因此保险起见留下了很多冗余
            for surClass in self.survivorMembers:

                if surClass.status != "S":      # 当前没有被标记为 S Status 的生还者

                    surClass.check_S_Status_by_external( True )       # 生还者成员应当被标记为 S Status
                    surClass.check_status()     # 重新检查该生还者成员当前所处的 status, 理论上此时生还者成员可能的status取值只有 S 和 I
                
                surClass.belongSurvivorGroupLogic = self.survivorGroupLogic

        else:       # 满足退出S Logic的所有条件时

            if self.notIMemberNum == 0:     # 全员倒地或者挂边

                self.survivorGroupLogic = "I"       # 组别被标记为I

                for surClass in self.survivorMembers:
                    surClass.belongSurvivorGroupLogic = self.survivorGroupLogic

            else:

                RStatusNum = 0
                DStatusNum = 0
                BStatusNum = 0


                # --- 强制处于 S Status 的生还者退出 S Status, 之后对所有成员的Status取值进行计数 --- #
                
                for surClass in self.survivorMembers:

                    if surClass.status == "S":

                        surClass.check_S_Status_by_external( False )    # 生还者成员 不 应当被标记为 S Status 
                        surClass.check_status()     # 重新检查该生还者成员当前所处的 status

                    # 理论上此时生还者成员的status取值 不 可能为 S
                    
                    if surClass.status == "R":
                        RStatusNum += 1

                    elif surClass.status == "D":
                        DStatusNum += 1

                    elif surClass.status == "B":
                        BStatusNum += 1

                # Logic 标记的优先级 R > B > D

                if (float(RStatusNum) / self.memberNum) * 100.0 >= 50.0:        # 超过 (包含) 50%的生还者为R Status
                    self.survivorGroupLogic = "R"

                elif (float(BStatusNum) / self.memberNum) * 100.0 >= 50.0:      # 超过 (包含) 50%的生还者为B Status
                    self.survivorGroupLogic = "B"

                else:       # 上述所有判断条件均不满足的
                    self.survivorGroupLogic = "D"

                for surClass in self.survivorMembers:
                    surClass.belongSurvivorGroupLogic = self.survivorGroupLogic

        return self.survivorGroupLogic      # 返回更新后的当前logic取值
    

    
    def checkWhetherRequestTank():
        """
        检查是否满足申请在该组别类附近生成坦克的条件
        """
        










