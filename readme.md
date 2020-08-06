There are some places marked with `TODO`, which will be removed on mainnet. They exist currently for the convenience of testing.




## 关于ont与ontd的转换

#### 测试网 ONT-Decimal 合约hash:  2e0de81023ea6d32460244f29c57c84ce569e7b7

#### 1. Ont->ontD接口：

```
函数名: ont2ontd

参数fromAcct: 类型为address,含义为谁想把他ont转换成为ontd

参数ontAmount: 类型为interger,含义为谁把他多少个ont转换为ontd

实现逻辑：ontAmount个ont将会从fromAcct转出，进入合约帐户，同时合约会将ont*10^9个ontd增发给fromAcct帐户
```

#### 2. Ontd->ont接口：

```
函数名：ontd2ont

参数fromAcct: 类型为address,含义为谁想把他ontd转换成为ont

参数ontdAmount: 类型为interger,含义为谁把他多少个ontd转换为ont

实现逻辑：
	ontAmt = ontdAmount/10^9
	将ontAmt个ont转给fromAcct,同时从fromAcct中扣除ontAmt*10^9个ontd，即销毁
```

#### 3. 其他接口：

其他所有的接口服从[该文档](https://github.com/ontio/OEPs/blob/master/OEPS/OEP-4.mediawiki)
