from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from direct.task.Task import Task
from pandac.PandaModules import *

from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals


class BankGUI(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('BankGUI')

    def __init__(self, doneEvent, allowWithdraw = 1):
        backGeom = loader.loadModel('phase_3/models/gui/tt_m_gui_ups_panelBg')
        DirectFrame.__init__(self, relief=None, geom=backGeom, geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(1.66, 1, 1.4), pos=(0, 0, 0))
        self.initialiseoptions(BankGUI)
        self.doneEvent = doneEvent
        self.__transactionAmount = 0
        bankGuiModel = loader.loadModel('phase_3/models/gui/bank_GUI')
        jarGui = bankGuiModel.find('**/jar')
        arrowGui = loader.loadModel('phase_3/models/gui/create_a_toon_gui')
        bankModel = bankGuiModel.find('**/vault')
        okImageList = (
            bankGuiModel.find('**/Ok_UP'),
            bankGuiModel.find('**/Ok_DN'),
            bankGuiModel.find('**/Ok_RLVR')
        )
        cancelImageList = (
            bankGuiModel.find('**/Cancel_UP'),
            bankGuiModel.find('**/Cancel_DN'),
            bankGuiModel.find('**/Cancel_RLVR')
        )
        arrowImageList = (
            arrowGui.find('**/CrtATn_R_Arrow_UP'),
            arrowGui.find('**/CrtATn_R_Arrow_DN'),
            arrowGui.find('**/CrtATn_R_Arrow_RLVR'),
            arrowGui.find('**/CrtATn_R_Arrow_UP')
        )
        self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, pos=(-0.2, 0, -0.4), text=TTLocalizer.BankGuiCancel, text_scale=0.06, text_pos=(0, -0.1), image_scale=0.6, command=self.__cancel)
        self.okButton = DirectButton(parent=self, relief=None, image=okImageList, pos=(0.2, 0, -0.4), text=TTLocalizer.BankGuiOk, text_scale=0.06, text_pos=(0, -0.1), image_scale=0.6, command=self.__requestTransaction)
        self.jarDisplay = DirectLabel(parent=self, relief=None, pos=(-0.4, 0, 0), scale=0.7, text=str(base.localAvatar.getMoney()), text_scale=0.2, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0, -0.1, 0), image=jarGui, text_font=ToontownGlobals.getSignFont())
        self.bankDisplay = DirectLabel(parent=self, relief=None, pos=(0.4, 0, 0), scale=0.9, text=str(base.localAvatar.getBankMoney()), text_scale=0.2, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0, -0.1, 0), image=bankModel, image_pos=(0.025, 0, 0),image_scale=0.8, text_font=ToontownGlobals.getSignFont())
        self.depositArrow = DirectButton(parent=self, relief=None, image=arrowImageList, image_scale=(1, 1, 1), image3_color=Vec4(0.6, 0.6, 0.6, 0.25), pos=(0.01, 0, 0.15))
        self.withdrawArrow = DirectButton(parent=self, relief=None, image=arrowImageList, image_scale=(-1, 1, 1), image3_color=Vec4(0.6, 0.6, 0.6, 0.25), pos=(-0.01, 0, -0.15))
        self.depositArrow.bind(DGG.B1PRESS, self.__depositButtonDown)
        self.depositArrow.bind(DGG.B1RELEASE, self.__depositButtonUp)
        self.withdrawArrow.bind(DGG.B1PRESS, self.__withdrawButtonDown)
        self.withdrawArrow.bind(DGG.B1RELEASE, self.__withdrawButtonUp)
        self.accept('bankAsleep', self.__cancel)
        self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
        self.accept(localAvatar.uniqueName('bankMoneyChange'), self.__bankMoneyChange)
        if allowWithdraw:
            self.depositArrow.setPos(0.01, 0, 0.15)
            self.withdrawArrow.setPos(-0.01, 0, -0.15)
        else:
            self.depositArrow.setPos(0, 0, 0)
            self.withdrawArrow.hide()
        jarGui.removeNode()
        arrowGui.removeNode()
        bankGuiModel.removeNode()
        self.__updateTransaction(0)

    def destroy(self):
        taskMgr.remove(self.taskName('runCounter'))
        self.ignore(localAvatar.uniqueName('moneyChange'))
        self.ignore(localAvatar.uniqueName('bankMoneyChange'))

        DirectFrame.destroy(self)

    def __cancel(self):
        messenger.send(self.doneEvent, [0])

    def __requestTransaction(self):
        self.ignore(localAvatar.uniqueName('moneyChange'))
        self.ignore(localAvatar.uniqueName('bankMoneyChange'))
        messenger.send(self.doneEvent, [self.__transactionAmount])

    def __updateTransaction(self, amount):
        hitLimit = 0
        self.__transactionAmount += amount
        jarMoney = base.localAvatar.getMoney()
        maxJarMoney = base.localAvatar.getMaxMoney()
        bankMoney = base.localAvatar.getBankMoney()
        maxBankMoney = ToontownGlobals.MaxBankMoney
        self.__transactionAmount = min(self.__transactionAmount, jarMoney)
        self.__transactionAmount = min(self.__transactionAmount, maxBankMoney - bankMoney)
        self.__transactionAmount = -min(-self.__transactionAmount, maxJarMoney - jarMoney)
        self.__transactionAmount = -min(-self.__transactionAmount, bankMoney)
        newJarMoney = jarMoney - self.__transactionAmount
        newBankMoney = bankMoney + self.__transactionAmount
        if newJarMoney <= 0 or newBankMoney >= maxBankMoney:
            self.depositArrow['state'] = DGG.DISABLED
            hitLimit = 1
        else:
            self.depositArrow['state'] = DGG.NORMAL
        if newBankMoney <= 0 or newJarMoney >= maxJarMoney:
            self.withdrawArrow['state'] = DGG.DISABLED
            hitLimit = 1
        else:
            self.withdrawArrow['state'] = DGG.NORMAL
        self.jarDisplay['text'] = str(newJarMoney)
        self.bankDisplay['text'] = str(newBankMoney)
        return (hitLimit, newJarMoney, newBankMoney, self.__transactionAmount)

    def __runCounter(self, task):
        if task.time - task.prevTime < task.delayTime:
            return Task.cont

        task.delayTime /= 2
        task.prevTime = task.time
        if task.delayTime < 0.005:
            task.amount *= 1.1
        hitLimit = self.__updateTransaction(int(task.amount))[0]
        if hitLimit:
            return Task.done

        return Task.cont

    def __depositButtonUp(self, event):
        messenger.send('wakeup')
        taskMgr.remove(self.taskName('runCounter'))

    def __depositButtonDown(self, event):
        messenger.send('wakeup')

        task = Task(self.__runCounter)
        task.delayTime = 0.2
        task.prevTime = 0.0
        task.amount = 1.0
        hitLimit = self.__updateTransaction(int(task.amount))[0]
        if not hitLimit:
            taskMgr.add(task, self.taskName('runCounter'))

    def __withdrawButtonUp(self, event):
        messenger.send('wakeup')
        taskMgr.remove(self.taskName('runCounter'))

    def __withdrawButtonDown(self, event):
        messenger.send('wakeup')

        task = Task(self.__runCounter)
        task.delayTime = 0.2
        task.prevTime = 0.0
        task.amount = -1.0
        hitLimit = self.__updateTransaction(int(task.amount))[0]
        if not hitLimit:
            taskMgr.add(task, self.taskName('runCounter'))

    def __moneyChange(self, money):
        self.__updateTransaction(0)

    def __bankMoneyChange(self, bankMoney):
        self.__updateTransaction(0)
