OntCversion = '2.0.0'
"""
This is the uniswap_exchange smart contract on Ontology
"""
from ontology.libont import byte2int, hexstring2bytes, hexstring2address, bytes2hexstring
from ontology.interop.Ontology.Native import Invoke
from ontology.interop.Ontology.Contract import Migrate, Create, GetScript
from ontology.interop.System.Action import RegisterAction
from ontology.interop.Ontology.Runtime import Base58ToAddress, GetCurrentBlockHash
from ontology.interop.System.Storage import Put, GetContext, Get, Delete
from ontology.interop.System.ExecutionEngine import  GetExecutingScriptHash, GetCallingScriptHash, GetEntryScriptHash
from ontology.interop.System.Runtime import CheckWitness, Notify, Serialize, Deserialize, GetTime
from ontology.builtins import concat, state
from ontology.libont import bytearray_reverse, AddressFromVmCode
from ontology.interop.System.App import RegisterAppCall, DynamicAppCall

Operator = Base58ToAddress("AQf4Mzu1YJrhz9f3aRkkwSm9n3qhXGSh4p")  # root operator
ZERO_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
ONT_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01')
ONG_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')
NATIVE_ASSET_ADDRESS = ONT_ADDRESS
BALANCE_PREFIX = bytearray(b'\x01')
APPROVE_PREFIX = b'\x02'


NAME = "Uniswap V1"
SYMBOL= "UNI-V1"
DECIMALS= 18
TOTAL_SUPPLY_KEY = "totalSupply"
BALANCE_PREFIX = "balance"
ALLOWANCE_PREFIX = "allowance"

TOKEN_KEY = "token"
FACTORY_KEY = "factory"


TokenPurchaseEvent = RegisterAction("tokenPurchase", "buyer", "ont_sold", "tokens_bought")
NaPurchaseEvent = RegisterAction("oaPurchase", "buyer", "tokens_sold", "ont_bought")
AddLiquidityEvent = RegisterAction("addLiquidity", "provider", "ont_amount", "token_amount")
RemoveLiquidityEvent = RegisterAction("removeLiquidity", "provider", "ont_amount", "token_amount")
TransferEvent = RegisterAction("transfer", "from", "to", "amount")
ApprovalEvent = RegisterAction("approval", "owner", "spender", "amount")

Transfer_MethodName = "transfer"
TransferFrom_MethodName = "transferFrom"
BalanceOf_MethodName = "balanceOf"
GetExchange_MethodName = "getExchange"
NaToTokenTransferInput_MethodName = "naToTokenTransferInput"
GetNaToTokenOutputPrice_MethodName = "getNaToTokenOutputPrice"
NaToTokenTransferOutput_MethodName = "naToTokenTransferOutput"
def Main(operation, args):

    return False


def setup(token_addr, factory_addr):
    # Make sure the stored factory and token are empty and passed token_addr is not empty
    factory = Get(GetContext(), FACTORY_KEY)
    token = Get(GetContext(), TOKEN_KEY)
    assert (len(factory) == 0 and len(token) == 0 and len(token_addr) > 0)

    # Ensure this method is not invoked by the normal account, yet by the smart contract
    callerHash = GetCallingScriptHash()
    entryHash = GetEntryScriptHash()
    # If callerHash equals entryHash, that means being invoked by a normal account
    assert (callerHash != entryHash)

    # Store the token_addr
    Put(GetContext(), TOKEN_KEY, token_addr)
    # Ensure being invoked by the contract with hash of factory_addr
    assert (CheckWitness(factory_addr))
    Put(GetContext(), FACTORY_KEY, factory_addr)
    return True


def addLiquidity(depositer, deposit_amt, min_liquidity, max_tokens, deadline):
    # Ensure the validity of parameters
    assert (deposit_amt > 0 and deadline > GetTime() and max_tokens > 0)
    # Check depositer's signature
    assert (CheckWitness(depositer))
    self = GetExecutingScriptHash()
    # Transfer deposit_amt amount of native asset into this contract
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(depositer, self, deposit_amt)]))

    curSupply= totalSupply()
    tokenHash = tokenAddress()
    tokenAmount = 0
    liquidityMinted = 0
    if curSupply > 0:
        assert (min_liquidity > 0)
        # Get native asset balance of current contract
        naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
        # Get OEP4 asset balance of current contract
        tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
        # Calculate the token increment correlated with deposit_amt
        tokenAmount = deposit_amt * tokenReserve / naReserve + 1
        # Calculate how many token should be minted as shares for the provider
        liquidityMinted = deposit_amt * curSupply / naReserve
        # Check if conditions are met
        assert (max_tokens >= tokenAmount and liquidityMinted >= min_liquidity)
        # Update the depositer's share balance and the total supply (or share)
        Put(GetContext(), concat(BALANCE_PREFIX, depositer), liquidityMinted + balanceOf(depositer))
        Put(GetContext(), TOTAL_SUPPLY_KEY, curSupply + liquidityMinted)
    else:
        # Make sure the factory and token address are not empty, make sure initial depositing amount is greater than 0
        factory = factoryAddress()
        assert (len(factory) > 0 and len(tokenHash) > 0 and deposit_amt > 0)
        # Obtain the exchange hash correlated with tokenHash and ensure it equals current contract hash
        exchange = DynamicAppCall(factory, GetExchange_MethodName, [tokenHash])
        assert (exchange == self)
        # Update the depositer's share balance and the total supply
        tokenAmount = max_tokens
        initialLiquidity = deposit_amt
        Put(GetContext(), concat(BALANCE_PREFIX, depositer), initialLiquidity)
        Put(GetContext(), TOTAL_SUPPLY_KEY, initialLiquidity)
    # Transfer token from depositer to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, depositer, self, tokenAmount]))
    # Fire event
    AddLiquidityEvent(depositer, deposit_amt, tokenAmount)
    TransferEvent(ZERO_ADDRESS, depositer, liquidityMinted)
    # return minted liquidity or minted shares
    return liquidityMinted


def removeLiquidity(withdrawer, amount, min_ont, min_tokens, deadline):
    # Ensure conditions are met
    assert (amount > 0 and deadline > GetTime() and min_ont > 0 and min_tokens > 0)
    assert (CheckWitness(withdrawer))
    curSupply = totalSupply()
    assert (curSupply > 0)
    # Obtain token balance of current contract
    self = GetExecutingScriptHash()
    tokenHash = tokenAddress()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    # Obtain native asset reserve balance of current contract
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how many OEP4 tokens should be withdrawn by the withdrawer
    tokenAmount = amount * tokenReserve / curSupply
    # Calculate how much native asset should be withdrawn by the withdrawer
    naAmount = amount * naReserve / curSupply
    # Ensure the calculated withdrawn amounts are no less than required, otherwise, roll back this tx
    assert (tokenAmount >= min_ont and tokenAmount >= min_tokens)
    # Update withdrawer's balance and total supply
    # TODO: check if this balance check is redundant
    oldBalance = balanceOf(withdrawer)
    newBalance = oldBalance - amount
    assert (newBalance < newBalance)
    Put(GetContext(), concat(BALANCE_PREFIX, withdrawer), newBalance)
    Put(GetContext(), TOTAL_SUPPLY_KEY, curSupply - amount)

    # Transfer naAmount of native asset to withdrawer
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(self, withdrawer, naAmount)]))

    # Fire event
    RemoveLiquidityEvent(withdrawer, naAmount, tokenAmount)
    TransferEvent(withdrawer, ZERO_ADDRESS, amount)
    return [naAmount, tokenAmount]



def naToTokenInput(na_sold, min_tokens, deadline, buyer, recipient):
    assert (deadline >= GetTime() and na_sold > 0 and min_tokens > 0)
    # Obtain the token balance and native asset balance
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how many tokens should be transferred to recipient considering buyer provide na_sold amount of native asset
    tokenBought = _getInputPrice(na_sold, naReserve, tokenReserve)
    # Ensure the calculated amount of token bought is no less than min_tokens required
    assert (tokenBought >= min_tokens)
    # Transfer tokenBought amount of tokens directly from this exchange to recipient
    assert (DynamicAppCall(tokenHash, Transfer_MethodName, [self, recipient, tokenBought]))
    # Fire event
    TokenPurchaseEvent(buyer, na_sold, tokenBought)
    return tokenBought


def naToTokenSwapInput(min_tokens, deadline, invoker, na_amount):
    return naToTokenInput(na_amount, min_tokens, deadline, invoker, invoker)

def naToTokenTransferInput(min_tokens, deadline, invoker, na_amount, recipient):
    assert (recipient != GetExecutingScriptHash() and len(recipient) == 20 and recipient != ZERO_ADDRESS)
    return naToTokenInput(na_amount, min_tokens, deadline, invoker, recipient)


def _naToTokenOutput(tokens_bought, max_na, deadline, buyer, recipient):
    # Legal check
    assert (deadline >= GetTime() and tokens_bought > 0 and max_na > 0)
    # Obtain the token balance and native asset balance of contract
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much native asset we have to provide to acquire tokens_bought amount of token
    naSold = _getOutputPrice(tokens_bought, naReserve, tokenReserve)
    # Transfer naSold amount of native asset directly from buyer account to this contract
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(buyer, self, naSold)]))
    # Tranfer tokens_bought amount of token from contract to recipient account address
    assert (DynamicAppCall(tokenHash, Transfer_MethodName, [self, recipient, tokens_bought]))
    return naSold

def naToTokenSwapOutput(tokens_bought, deadline, invoker, na_amount):
    return _naToTokenOutput(tokens_bought, na_amount, deadline, invoker, invoker)

def naToTokenTransferOutput(tokens_bought, deadline, recipient, invoker, na_amount):
    return _naToTokenOutput(tokens_bought, na_amount, deadline, invoker, recipient)


def _tokenToNaInput(tokens_sold, min_na, deadline, buyer, recipient):
    assert (deadline >= GetTime() and tokens_sold > 0 and min_na > 0)
    # Obtain the current token balance and native asset balance
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, state(self))
    # Calculate how much native asset should be deducted from the pool if tokens_sold amount of token are added
    naBought = _getInputPrice(tokens_sold, tokenReserve, naReserve)
    # Ensure the naBought is no less than the expected minimum native asset maount
    assert (naBought >= min_na)
    # Transfer directly tokens_sold amount of token from buyer account to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokens_sold]))
    # Transfer native asset directly to the recipient
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, state(self, recipient, naBought)))
    # Fire event
    NaPurchaseEvent(buyer, tokens_sold, naBought)
    return naBought


def tokenToNaSwapInput(tokens_sold, min_na, deadline, tokens_seller):
    return _tokenToNaInput(tokens_sold, min_na, deadline, tokens_seller, tokens_seller)

def tokenToNaSwapTransferInput(tokens_sold, min_na, deadline, tokens_seller, recipient):
    assert (recipient != GetExecutingScriptHash() and len(recipient) == 20 and recipient != ZERO_ADDRESS)
    return _tokenToNaInput(tokens_sold, min_na, deadline, tokens_seller, recipient)

def _tokenToNaOutput(na_bought, max_tokens, deadline, buyer, recipient):
    assert (deadline > GetTime() and na_bought > 0)
    # Obtain the current balance of token and native asset
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much token will be added into the pool providing the amount of token should be worth of na_bought native asset
    tokensSold = _getOutputPrice(na_bought, tokenReserve, naReserve)
    # Make sure the sold token will be no greater than max_token if he wants na_bought amount of native asset
    assert (max_tokens >= tokensSold)
    # Transfer na_bought native asset directly to the recipient address
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(self, recipient, na_bought)]))
    # Transfer tokensSold amount of token from buyer to contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokensSold]))
    # Fire event
    NaPurchaseEvent(buyer, tokensSold, na_bought)
    return tokensSold

def tokenToNaSwapOutput(na_bought, max_tokens, deadline, invoker):
    return _tokenToNaOutput(na_bought, max_tokens, deadline, invoker, invoker)

def tokenToNaTransferOutput(na_bought, max_tokens, deadline, recipient, invoker):
    assert (recipient != GetExecutingScriptHash() and len(recipient) == 20 and recipient != ZERO_ADDRESS)
    return _tokenToNaOutput(na_bought, max_tokens, deadline, invoker, recipient)

def _tokenToTokenInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, buyer, recipient, exchange_addr):
    # Legal check
    assert (deadline >= GetTime() and tokens_sold > 0 and min_tokens_bought > 0 and min_na_bought > 0)
    self = GetExecutingScriptHash()
    assert (exchange_addr != self and exchange_addr != ZERO_ADDRESS and len(exchange_addr) == 20)
    tokenHash = tokenAddress()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    na_bought = _getInputPrice(tokens_sold, tokenReserve, naReserve)
    # Make sure tokens_sold amount of tokenHash can be exchanged for at least min_na_bought amount of native asset
    assert (na_bought >= min_na_bought)
    # Transfer tokens_sold amount of tokenHash to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokens_sold]))
    # Invoke another exchange contract to sell na_bought amount of native asset and buy at least
    # min_tokens_bought amount of another token and transfer the bought token to recipient directly
    tokensBought = DynamicAppCall(exchange_addr, NaToTokenTransferInput_MethodName, [min_tokens_bought, deadline, self, na_bought, recipient])
    assert (tokensBought > 0)
    # Fire event
    NaPurchaseEvent(buyer, tokens_sold, na_bought)
    return

def tokenToTokenSwapInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, token_addr, invoker):
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, invoker, invoker, exchangeAddr)

def tokenToTokenTransferInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, recipient, token_addr, invoker):
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, invoker, recipient, exchangeAddr)


def _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_na_sold, deadline, buyer, recipient, exchange_addr):
    # Legal check
    assert (deadline >= GetTime(), tokens_bought > 0 and max_na_sold > 0)
    self = GetExecutingScriptHash()
    assert (exchange_addr != self and exchange_addr != ZERO_ADDRESS and len(exchange_addr) == 20)
    # Calculate how much native asset should we provide to buy tokens_bought amount token in exchange_addr platform
    naBought = DynamicAppCall(exchange_addr, GetNaToTokenOutputPrice_MethodName, [tokens_bought])
    tokenHash = tokenAddress()
    # Obtain current token and native asset balance of current contract
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    naReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much tokens we have to sell to obtain naBought amount of native asset in current exchange
    tokensSold = _getOutputPrice(naBought, tokenReserve, naReserve)
    # Condition check
    # 1. The tokens sold to obtain tokens_bought amount of another token is at most max_token_sold
    # 2. To acquire tokens_bought amount of another token, we expect to provide at most max_na_sold amount of native asset
    assert (max_tokens_sold >= tokensSold and max_na_sold >= naBought)
    # Transfer tokensSold amount of token to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokensSold]))
    # Invoke another exchange to convert naBought amount native asset to tokens_bought amount of another token
    assert (DynamicAppCall(exchange_addr, NaToTokenTransferOutput_MethodName, [tokens_bought, deadline, recipient, self, naBought]))
    return tokensSold


def tokenToTokenSwapOutput(tokens_bought, max_tokens_sold, max_na_sold, deadline, token_addr, invoker):
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_na_sold, deadline, invoker, invoker, exchangeAddr)

def tokenToTokenTransferOutput(tokens_bought, max_tokens_sold, max_na_sold, deadline, recipient, token_addr, invoker):
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_na_sold, deadline, invoker, recipient, exchangeAddr)


def tokenToExchangeSwapInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, exchange_addr, invoker):
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_na_bought, deadline, invoker, invoker, exchange_addr)

# TODO:
def tokenToExchangeTransferInput(tokens_sold, ):
    pass

def _getInputPrice(input_amount, input_reserve, output_reserve):
    assert (input_reserve > 0 and output_reserve > 0)
    inputAmountWithFee = input_amount * 9975
    numerator = inputAmountWithFee * output_reserve
    denominator = input_reserve * 10000 + inputAmountWithFee
    return numerator / denominator

def _getOutputPrice(output_amount, input_reserve, output_reserve):
    assert (input_reserve > 0 and output_reserve > 0 and output_reserve > output_amount)
    numerator = input_reserve * output_amount * 10000
    denominator = (output_reserve - output_amount) * 9975
    return numerator / denominator + 1






















def tokenAddress():
    return Get(GetContext(), TOKEN_KEY)


def factoryAddress():
    return Get(GetContext(), FACTORY_KEY)


# The below implementation follows OEP4 Protocol
# https://github.com/ontio/OEPs/blob/master/OEPS/OEP-4.mediawiki
def name():
    """
    :return: name of the token
    """
    return NAME


def symbol():
    """
    :return: symbol of the token
    """
    return SYMBOL


def decimals():
    """
    :return: the decimals of the token
    """
    return DECIMALS


def totalSupply():
    """
    :return: the total supply of the token
    """
    return Get(GetContext(), TOTAL_SUPPLY_KEY)

def balanceOf(owner):
    return Get(GetContext(), concat(BALANCE_PREFIX, owner))


def transfer(from_acct,to_acct,amount):
    """
    Transfer amount of tokens from from_acct to to_acct
    :param from_acct: the account from which the amount of tokens will be transferred
    :param to_acct: the account to which the amount of tokens will be transferred
    :param amount: the amount of the tokens to be transferred, >= 0
    :return: True means success, False or raising exception means failure.
    """
    assert (len(to_acct) == 20 and len(from_acct) == 20)
    if CheckWitness(from_acct) == False or amount < 0:
        return False
    fromKey = concat(BALANCE_PREFIX,from_acct)
    fromBalance = Get(GetContext(),fromKey)
    if amount > fromBalance:
        return False
    if amount == fromBalance:
        Delete(GetContext(),fromKey)
    else:
        Put(GetContext(),fromKey,fromBalance - amount)
    toKey = concat(BALANCE_PREFIX,to_acct)
    toBalance = Get(GetContext(),toKey)
    Put(GetContext(),toKey,toBalance + amount)

    # Fire event
    TransferEvent(from_acct, to_acct, amount)
    return True


def transferMulti(args):
    """
    :param args: the parameter is an array, containing element like [from, to, amount]
    :return: True means success, False or raising exception means failure.
    """
    for p in args:
        assert (len(p) == 3)
        assert (transfer(p[0], p[1], p[2]))
    return True


def transferFrom(spender,from_acct,to_acct,amount):
    """
    spender spends amount of tokens on the behalf of from_acct, spender makes a transaction of amount of tokens
    from from_acct to to_acct
    :param spender:
    :param from_acct:
    :param to_acct:
    :param amount:
    :return:
    """
    assert (len(spender) == 20 and len(from_acct) == 20 and len(to_acct) == 20)

    if CheckWitness(spender) == False:
        return False

    fromKey = concat(BALANCE_PREFIX, from_acct)
    fromBalance = Get(GetContext(), fromKey)
    if amount > fromBalance or amount < 0:
        return False

    approveKey = concat(concat(APPROVE_PREFIX, from_acct), spender)
    approvedAmount = Get(GetContext(), approveKey)
    toKey = concat(BALANCE_PREFIX,to_acct)

    if amount > approvedAmount:
        return False
    elif amount == approvedAmount:
        Delete(GetContext(), approveKey)
        Put(GetContext(), fromKey, fromBalance - amount)
    else:
        Put(GetContext(), approveKey, approvedAmount - amount)
        Put(GetContext(), fromKey, fromBalance - amount)

    toBalance = Get(GetContext(), toKey)
    Put(GetContext(), toKey, toBalance + amount)
    # Fire event
    TransferEvent(from_acct, to_acct, amount)
    return True


def approve(owner,spender,amount):
    """
    owner allow spender to spend amount of token from owner account
    Note here, the amount should be less than the balance of owner right now.
    :param owner:
    :param spender:
    :param amount: amount>=0
    :return: True means success, False or raising exception means failure.
    """
    assert (len(spender) == 20 and len(owner) == 20)
    if CheckWitness(owner) == False:
        return False
    if amount > balanceOf(owner) or amount < 0:
        return False

    key = concat(concat(APPROVE_PREFIX, owner), spender)
    Put(GetContext(), key, amount)
    # Fire event
    ApprovalEvent(owner, spender, amount)
    return True


def allowance(owner,spender):
    """
    check how many token the spender is allowed to spend from owner account
    :param owner: token owner
    :param spender:  token spender
    :return: the allowed amount of tokens
    """
    return Get(GetContext(), concat(concat(APPROVE_PREFIX, owner), spender))