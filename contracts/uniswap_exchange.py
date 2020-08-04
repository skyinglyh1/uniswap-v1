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

ZERO_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
ONT_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01')
ONG_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')
NATIVE_ASSET_ADDRESS = ONG_ADDRESS

NAME = "Uniswap V1"
SYMBOL= "UNI-V1"
DECIMALS= 9
TOTAL_SUPPLY_KEY = "totalSupply"
BALANCE_PREFIX = "balance"
APPROVE_PREFIX = "allowance"

TOKEN_KEY = "token"
FACTORY_KEY = "factory"

# Event format
SetupEvent = RegisterAction("setup", "token_addr", "factory_addr")
TokenPurchaseEvent = RegisterAction("tokenPurchase", "buyer", "ont_sold", "tokens_bought")
OngPurchaseEvent = RegisterAction("ongPurchase", "buyer", "tokens_sold", "ont_bought")
AddLiquidityEvent = RegisterAction("addLiquidity", "provider", "ont_amount", "token_amount")
RemoveLiquidityEvent = RegisterAction("removeLiquidity", "provider", "ont_amount", "token_amount")
TransferEvent = RegisterAction("transfer", "from", "to", "amount")
ApprovalEvent = RegisterAction("approval", "owner", "spender", "amount")

# Method name used for Invoke or DynamicAppCall
Transfer_MethodName = "transfer"
TransferFrom_MethodName = "transferFrom"
BalanceOf_MethodName = "balanceOf"
GetExchange_MethodName = "getExchange"
OngToTokenTransferInput_MethodName = "ongToTokenTransferInput"
GetNaToTokenOutputPrice_MethodName = "getNaToTokenOutputPrice"
OngToTokenTransferOutput_MethodName = "ongToTokenTransferOutput"

def Main(operation, args):
    if operation == "setup":
        assert (len(args) == 2)
        token_addr = args[0]
        factory_addr = args[1]
        return setup(token_addr, factory_addr)
    if operation == "addLiquidity":
        assert (len(args) == 5)
        min_liquidity = args[0]
        max_tokens = args[1]
        deadline = args[2]
        depositer = args[3]
        deposit_ong_amt = args[4]
        return addLiquidity(min_liquidity, max_tokens, deadline, depositer, deposit_ong_amt)
    if operation == "removeLiquidity":
        assert (len(args) == 5)
        amount = args[0]
        min_ong = args[1]
        min_tokens = args[2]
        deadline = args[3]
        withdrawer = args[4]
        return removeLiquidity(amount, min_ong, min_tokens, deadline, withdrawer)
    if operation == "ongToTokenSwapInput":
        assert (len(args) == 4)
        min_tokens = args[0]
        deadline = args[1]
        invoker = args[2]
        ong_amount = args[3]
        return ongToTokenSwapInput(min_tokens, deadline, invoker, ong_amount)
    if operation == "ongToTokenTransferInput":
        assert (len(args) == 5)
        min_tokens = args[0]
        deadline = args[1]
        recipient = args[2]
        invoker = args[3]
        ong_amount = args[4]
        return ongToTokenTransferInput(min_tokens, deadline, recipient, invoker, ong_amount)
    if operation == "ongToTokenSwapOutput":
        assert (len(args) == 4)
        tokens_bought = args[0]
        deadline = args[1]
        invoker = args[2]
        ong_amount = args[3]
        return ongToTokenSwapOutput(tokens_bought, deadline, invoker, ong_amount)
    if operation == "ongToTokenTransferOutput":
        assert (len(args) == 5)
        tokens_bought = args[0]
        deadline = args[1]
        recipient = args[2]
        invoker = args[3]
        ong_amount = args[4]
        return ongToTokenTransferOutput(tokens_bought, deadline, recipient, invoker, ong_amount)
    if operation == "tokenToOngSwapInput":
        assert (len(args) == 4)
        tokens_sold = args[0]
        min_ong = args[1]
        deadline = args[2]
        tokens_seller = args[3]
        return tokenToOngSwapInput(tokens_sold, min_ong, deadline, tokens_seller)
    if operation == "tokenToOngSwapTransferInput":
        assert (len(args) == 5)
        tokens_sold = args[0]
        min_ong = args[1]
        deadline = args[2]
        tokens_seller = args[3]
        recipient = args[4]
        return tokenToOngSwapTransferInput(tokens_sold, min_ong, deadline, tokens_seller, recipient)
    if operation == "tokenToOngSwapOutput":
        assert (len(args) == 4)
        ong_bought = args[0]
        max_tokens = args[1]
        deadline = args[2]
        invoker = args[3]
        return tokenToOngSwapOutput(ong_bought, max_tokens, deadline, invoker)
    if operation == "tokenToOngTransferOutput":
        assert (len(args) == 5)
        ong_bought = args[0]
        max_tokens = args[1]
        deadline = args[2]
        recipient = args[3]
        invoker = args[4]
        return tokenToOngTransferOutput(ong_bought, max_tokens, deadline, recipient, invoker)
    if operation == "tokenToTokenSwapInput":
        assert (len(args) == 6)
        tokens_sold = args[0]
        min_tokens_bought = args[1]
        min_ong_bought = args[2]
        deadline = args[3]
        token_addr = args[4]
        invoker = args[5]
        return tokenToTokenSwapInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, token_addr, invoker)
    if operation == "tokenToTokenTransferInput":
        assert (len(args) == 7)
        tokens_sold = args[0]
        min_tokens_bought = args[1]
        min_ong_bought = args[2]
        deadline = args[3]
        recipient = args[4]
        token_addr = args[5]
        invoker = args[6]
        return tokenToTokenTransferInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, recipient, token_addr, invoker)
    if operation == "tokenToTokenSwapOutput":
        assert (len(args) == 6)
        tokens_bought = args[0]
        max_tokens_sold = args[1]
        max_ong_sold = args[2]
        deadline = args[3]
        token_addr = args[4]
        invoker = args[5]
        return tokenToTokenSwapOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, token_addr, invoker)
    if operation == "tokenToTokenTransferOutput":
        assert (len(args) == 7)
        tokens_bought = args[0]
        max_tokens_sold = args[1]
        max_ong_sold = args[2]
        deadline = args[3]
        recipient = args[4]
        token_addr = args[5]
        invoker = args[6]
        return tokenToTokenTransferOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, recipient, token_addr, invoker)
    if operation == "tokenToExchangeSwapInput":
        assert (len(args) == 6)
        tokens_sold = args[0]
        min_tokens_bought = args[1]
        min_ong_bought = args[2]
        deadline = args[3]
        exchange_addr = args[4]
        invoker = args[5]
        return tokenToExchangeSwapInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, exchange_addr, invoker)
    if operation == "tokenToExchangeTransferInput":
        assert (len(args) == 7)
        tokens_sold = args[0]
        min_tokens_bought = args[1]
        min_ong_bought = args[2]
        deadline = args[3]
        recipient = args[4]
        exchange_addr = args[5]
        invoker = args[6]
        return tokenToExchangeTransferInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, recipient, exchange_addr, invoker)
    if operation == "tokenToExchangeSwapOutput":
        assert (len(args) == 6)
        tokens_bought = args[0]
        max_tokens_sold = args[1]
        max_ong_sold = args[2]
        deadline = args[3]
        exchange_addr = args[4]
        invoker = args[5]
        return tokenToExchangeSwapOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, exchange_addr, invoker)
    if operation == "tokenToExchangeTransferOutput":
        assert (len(args) == 7)
        tokens_bought = args[0]
        max_tokens_sold = args[1]
        max_ong_sold = args[2]
        deadline = args[3]
        recipient = args[4]
        exchange_addr = args[5]
        invoker = args[6]
        return tokenToExchangeTransferOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, recipient, exchange_addr, invoker)
    if operation == "getOngToTokenInputPrice":
        assert (len(args) == 1)
        ong_sold = args[0]
        return getOngToTokenInputPrice(ong_sold)
    if operation == "getOngToTokenOutputPrice":
        assert (len(args) == 1)
        tokens_bought = args[0]
        return getOngToTokenOutputPrice(tokens_bought)
    if operation == "getTokenToOngInputPrice":
        assert (len(args) == 1)
        tokens_sold = args[0]
        return getTokenToOngInputPrice(tokens_sold)
    if operation == "getTokenToOngOutputPrice":
        assert (len(args) == 1)
        ong_bought = args[0]
        return getTokenToOngOutputPrice(ong_bought)
    if operation == "tokenAddress":
        return tokenAddress()
    if operation == "factoryAddress":
        return factoryAddress()

    if operation == "name":
        return name()
    if operation == "symbol":
        return symbol()
    if operation == "decimals":
        return decimals()
    if operation == "totalSupply":
        return totalSupply()
    if operation == "balanceOf":
        assert (len(args) == 1)
        owner = args[0]
        return balanceOf(owner)
    if operation == "transfer":
        assert (len(args) == 3)
        from_acct = args[0]
        to_acct = args[1]
        amount = args[2]
        return transfer(from_acct, to_acct, amount)
    if operation == "transferMulti":
        return transferMulti(args)
    if operation == "transferFrom":
        assert (len(args) == 4)
        spender = args[0]
        from_acct = args[1]
        to_acct = args[2]
        amount = args[3]
        return transferFrom(spender, from_acct, to_acct, amount)
    if operation == "approve":
        assert (len(args) == 3)
        owner = args[0]
        spender = args[1]
        amount = args[2]
        return approve(owner, spender, amount)
    if operation == "allowance":
        assert (len(args) == 2)
        owner = args[0]
        spender = args[1]
        return allowance(owner, spender)
    return False


def setup(token_addr, factory_addr):
    """
    This function is called once by the factory contract during contract creation.
    :param token_addr: Indicate which token is supported by current exchange contract, token_addr -> reversed token contract hash
    :param factory_addr: Indicate contract address which is invoking `setup` method, factory_addr -> reversed factory contract hash
    :return:
    """
    # Make sure the stored factory and token are empty and passed token_addr is not empty
    factory = Get(GetContext(), FACTORY_KEY)
    token = Get(GetContext(), TOKEN_KEY)
    assert (len(factory) == 0 and len(token) == 0 and len(token_addr) == 20 and len(factory_addr) == 20)
    # Ensure being invoked by the contract with hash of factory_addr
    assert (CheckWitness(factory_addr))
    # Ensure this method is not invoked by the normal account, yet by the smart contract
    callerHash = GetCallingScriptHash()
    entryHash = GetEntryScriptHash()
    # If callerHash equals entryHash, that means being invoked by a normal account
    assert (callerHash != entryHash)

    # Store the token_addr
    Put(GetContext(), TOKEN_KEY, token_addr)
    Put(GetContext(), FACTORY_KEY, factory_addr)

    # Fire event
    SetupEvent(token_addr, factory_addr)
    return True


def addLiquidity(min_liquidity, max_tokens, deadline, depositer, deposit_ong_amt):
    """
    Deposit ONG and Tokens at current ratio to mint UNI tokens

    :param min_liquidity: Condition check to help depositer define minimum share minted to himself
    :param max_tokens: Maximum number of tokens deposited. Deposits max amount if total UNI supply is 0
    :param deadline: Time after which this transaction can no longer be executed.
    :param depositer: Account address depositing Ong and tokens into contract to add liquidity
    :param deposit_ong_amt: Amount of ont that will be deposited
    :return: The amount of UNI minted
    """
    # Ensure the validity of parameters
    assert (deposit_ong_amt > 0 and deadline > GetTime() and max_tokens > 0)
    # Check depositer's signature
    assert (CheckWitness(depositer))
    self = GetExecutingScriptHash()
    # Transfer deposit_amt amount of native asset into this contract
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(depositer, self, deposit_ong_amt)]))

    curSupply= totalSupply()
    tokenAddr = tokenAddress()
    tokenAmount = 0
    liquidityMinted = 0
    if curSupply > 0:
        assert (min_liquidity > 0)
        # Get native asset ong balance of current contract
        ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
        # Get OEP4 asset balance of current contract
        tokenReserve = DynamicAppCall(tokenAddr, BalanceOf_MethodName, [self])
        # Calculate the token increment correlated with deposit_ong_amt
        tokenAmount = deposit_ong_amt * tokenReserve / ongReserve + 1
        # Calculate how many token should be minted as shares for the provider
        liquidityMinted = deposit_ong_amt * curSupply / ongReserve
        # Check if conditions are met
        assert (max_tokens >= tokenAmount and liquidityMinted >= min_liquidity)
        # Update the depositer's share balance and the total supply (or share)
        Put(GetContext(), concat(BALANCE_PREFIX, depositer), liquidityMinted + balanceOf(depositer))
        Put(GetContext(), TOTAL_SUPPLY_KEY, curSupply + liquidityMinted)
    else:
        # Make sure the factory and token address are not empty, make sure initial depositing amount is greater than 0
        factory = factoryAddress()
        assert (len(factory) > 0 and len(tokenAddr) > 0 and deposit_ong_amt > 0)
        # Obtain the exchange hash correlated with tokenHash and ensure it equals current contract hash
        exchange = DynamicAppCall(factory, GetExchange_MethodName, [bytearray_reverse(tokenAddr)])
        assert (exchange == self)
        # Update the depositer's share balance and the total supply
        tokenAmount = max_tokens
        initialLiquidity = deposit_ong_amt
        Put(GetContext(), concat(BALANCE_PREFIX, depositer), initialLiquidity)
        Put(GetContext(), TOTAL_SUPPLY_KEY, initialLiquidity)
    # Transfer token from depositer to current contract
    assert (DynamicAppCall(tokenAddr, TransferFrom_MethodName, [self, depositer, self, tokenAmount]))
    # Fire event
    AddLiquidityEvent(depositer, deposit_ong_amt, tokenAmount)
    TransferEvent(ZERO_ADDRESS, depositer, liquidityMinted)
    # return minted liquidity or minted shares
    return liquidityMinted


def removeLiquidity(amount, min_ong, min_tokens, deadline, withdrawer):
    """
    Burn UNI tokens to withdraw ETH and Tokens at current ratio

    :param amount: Amount of UNI burned
    :param min_ong: Minimum Ong withdrawn
    :param min_tokens: Minimum tokens withdrawn
    :param deadline: Time after which this transaction can no longer be executed
    :param withdrawer: Account address who wants to remove his shares of Ong and tokens from liquidity pool
    :return: The amount of Ong and tokens withdrawn
    """
    # Ensure conditions are met
    assert (amount > 0 and deadline > GetTime() and min_ong > 0 and min_tokens > 0)
    assert (CheckWitness(withdrawer))
    curSupply = totalSupply()
    assert (curSupply > 0)
    # Obtain token balance of current contract
    self = GetExecutingScriptHash()
    tokenAddr = tokenAddress()
    tokenReserve = DynamicAppCall(tokenAddr, BalanceOf_MethodName, [self])
    # Obtain native asset reserve balance of current contract
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how many OEP4 tokens should be withdrawn by the withdrawer
    tokenAmount = amount * tokenReserve / curSupply
    # Calculate how much native asset should be withdrawn by the withdrawer
    ongAmount = amount * ongReserve / curSupply
    # Ensure the calculated withdrawn amounts are no less than required, otherwise, roll back this tx
    assert (tokenAmount >= min_ong and tokenAmount >= min_tokens)
    # Update withdrawer's balance and total supply
    # TODO: check if this balance check is redundant
    oldBalance = balanceOf(withdrawer)
    newBalance = oldBalance - amount
    assert (newBalance < oldBalance)
    Put(GetContext(), concat(BALANCE_PREFIX, withdrawer), newBalance)
    Put(GetContext(), TOTAL_SUPPLY_KEY, curSupply - amount)

    # Transfer ongAmount of native asset to withdrawer
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(self, withdrawer, ongAmount)]))

    # Fire event
    RemoveLiquidityEvent(withdrawer, ongAmount, tokenAmount)
    TransferEvent(withdrawer, ZERO_ADDRESS, amount)
    return [ongAmount, tokenAmount]



def _ongToTokenInput(ong_sold, min_tokens, deadline, buyer, recipient):
    # Check signature of buyer
    assert (CheckWitness(buyer))
    assert (deadline >= GetTime() and ong_sold > 0 and min_tokens > 0)
    # Obtain the token balance and native asset balance
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how many tokens should be transferred to recipient considering buyer provide ong_sold amount of native asset ong
    tokenBought = _getInputPrice(ong_sold, ongReserve, tokenReserve)
    # Ensure the calculated amount of token bought is no less than min_tokens required
    assert (tokenBought >= min_tokens)
    # Transfer ong_sold amount of ong from buyer to self contract address
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(buyer, self, ong_sold)]))
    # Transfer tokenBought amount of tokens directly from this exchange to recipient
    assert (DynamicAppCall(tokenHash, Transfer_MethodName, [self, recipient, tokenBought]))
    # Fire event
    TokenPurchaseEvent(buyer, ong_sold, tokenBought)
    return tokenBought


def ongToTokenSwapInput(min_tokens, deadline, invoker, ong_amount):
    """
    Convert ong_amount of Ong to tokens and transfer tokens to invoker with conditions:
    1. tokens bought no less than min_tokens
    2. tx executed no late than deadline

    :param min_tokens: min_tokens invoker expects providing ong_amount of ong
    :param deadline: Time after which this transaction can no longer be executed
    :param invoker: The user's account address
    :param ong_amount: The amount of ong user provides
    :return: Amount of tokens bought
    """
    return _ongToTokenInput(ong_amount, min_tokens, deadline, invoker, invoker)

def ongToTokenTransferInput(min_tokens, deadline, recipient, invoker, ong_amount):
    """
    Convert Ong to tokens and transfer tokens to recipient with conditions:
    1. tokens bought no less than min_tokens
    2. tx executed no late than deadline

    :param min_tokens: Minimum token bought expected
    :param deadline: Time after which this tx will not be executed
    :param recipient: Address that will receive output tokens
    :param invoker: msg sender of this tx, account address wishing exchange ong for tokens
    :param ong_amount: Amount of Ong invoker provides to buy tokens
    :return:
    """
    assert (recipient != GetExecutingScriptHash() and len(recipient) == 20 and recipient != ZERO_ADDRESS)
    return _ongToTokenInput(ong_amount, min_tokens, deadline, invoker, recipient)


def _ongToTokenOutput(tokens_bought, max_ong, deadline, buyer, recipient):
    # Check signature of buyer
    assert (CheckWitness(buyer))
    # Legal check
    assert (deadline >= GetTime() and tokens_bought > 0 and max_ong > 0)
    # Obtain the token balance and native asset balance of contract
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much native asset we have to provide to acquire tokens_bought amount of token
    ongSold = _getOutputPrice(tokens_bought, ongReserve, tokenReserve)
    # Transfer ongSold amount of native asset directly from buyer account to this contract
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(buyer, self, ongSold)]))
    # Transfer tokens_bought amount of token from contract to recipient account address
    assert (DynamicAppCall(tokenHash, Transfer_MethodName, [self, recipient, tokens_bought]))
    return ongSold

def ongToTokenSwapOutput(tokens_bought, deadline, invoker, ong_amount):
    """
    Convert some Ong, yet less than ong_amount, to tokens_bought amount of tokens and transfer tokens to invoker with conditions:
    1. the spent ong amount should be no greater than ong_amount
    2. tx should not be executable after deadline

    :param tokens_bought: Exact amount of tokens bought
    :param deadline: Time after which this tx can no longer be executed
    :param invoker: User expecting to exchange with ong for tokens
    :param ong_amount: Amount of Maximum ong invoker provides for acquiring tokens_bought tokens
    :return: Amount of ong sold for obtaining tokens_bought amount of tokens
    """
    return _ongToTokenOutput(tokens_bought, ong_amount, deadline, invoker, invoker)

def ongToTokenTransferOutput(tokens_bought, deadline, recipient, invoker, ong_amount):
    """
    Convert some Ong, yet less than ong_amount, to tokens_bought amount of tokens and transfer tokens to recipient with conditions:
    1. the spent ong amount should be no greater than ong_amount
    2. tx should not be executable after deadline

    :param tokens_bought: Exact amount of tokens bought
    :param deadline: Time after which this tx can no longer be executed
    :param recipient: Aaddress that receives output Tokens.
    :param invoker: User expecting to exchange with ong for tokens
    :param ong_amount: Amount of Maximum ong invoker provides for acquiring tokens_bought tokens
    :return: Amount of ong sold for obtaining tokens_bought amount of tokens
    """
    return _ongToTokenOutput(tokens_bought, ong_amount, deadline, invoker, recipient)


def _tokenToOngInput(tokens_sold, min_ong, deadline, buyer, recipient):
    # Check the signature of buyer
    assert (CheckWitness(buyer))
    assert (deadline >= GetTime() and tokens_sold > 0 and min_ong > 0)
    # Obtain the current token balance and native asset balance
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much native asset should be deducted from the pool if tokens_sold amount of token are added
    ongBought = _getInputPrice(tokens_sold, tokenReserve, ongReserve)
    # Ensure the ongBought is no less than the expected minimum native asset ong amount
    assert (ongBought >= min_ong)
    # Transfer directly tokens_sold amount of token from buyer account to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokens_sold]))
    # Transfer native asset directly to the recipient
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, state(self, recipient, ongBought)))
    # Fire event
    OngPurchaseEvent(buyer, tokens_sold, ongBought)
    return ongBought


def tokenToOngSwapInput(tokens_sold, min_ong, deadline, tokens_seller):
    """
    Convert tokens_sold amount of tokens to Ong and transfer ong to tokens_seller with conditions:
    1. the converted ong should be no less than min_ong
    2. tx can no long be executed after deadline

    :param tokens_sold: Amount of tokens sold
    :param min_ong: Minimum Ong after converted
    :param deadline: Time after which this tx can no longer be executed
    :param tokens_seller: Account address who wishes convert tokens_sold amount token to some ong no less than min_ong
    :return: Amount of ong converted
    """
    return _tokenToOngInput(tokens_sold, min_ong, deadline, tokens_seller, tokens_seller)

def tokenToOngSwapTransferInput(tokens_sold, min_ong, deadline, tokens_seller, recipient):
    """
    Convert tokens_sold amount of tokens to Ong and transfer ong to recipient with conditions:
    1. the converted ong should be no less than min_ong
    2. tx can no long be executed after deadline

    :param tokens_sold: Amount of tokens sold
    :param min_ong: Minimum Ong after converted
    :param deadline: Time after which this tx can no longer be executed
    :param tokens_seller: Account address who wishes convert tokens_sold amount token to some ong no less than min_ong
    :param recipient: Address that receives output Ong
    :return:
    """
    assert (recipient != GetExecutingScriptHash() and len(recipient) == 20 and recipient != ZERO_ADDRESS)
    return _tokenToOngInput(tokens_sold, min_ong, deadline, tokens_seller, recipient)

def _tokenToOngOutput(ong_bought, max_tokens, deadline, buyer, recipient):
    # Check signature of buyer
    assert (CheckWitness(buyer))
    assert (deadline > GetTime() and ong_bought > 0)
    # Obtain the current balance of token and native asset
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much token will be added into the pool providing the amount of token should be worth of ong_bought native asset
    tokensSold = _getOutputPrice(ong_bought, tokenReserve, ongReserve)
    # Make sure the sold token will be no greater than max_token if he wants ong_bought amount of native asset
    assert (max_tokens >= tokensSold)
    # Transfer na_bought native asset directly to the recipient address
    assert (Invoke(0, NATIVE_ASSET_ADDRESS, Transfer_MethodName, [state(self, recipient, ong_bought)]))
    # Transfer tokensSold amount of token from buyer to contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokensSold]))
    # Fire event
    OngPurchaseEvent(buyer, tokensSold, ong_bought)
    return tokensSold

def tokenToOngSwapOutput(ong_bought, max_tokens, deadline, invoker):
    """
    Convert some tokens to specific ong_bought amount of ong and transfer ong to invoker with conditions
    1. the required amount of tokens equal to ong_bought should be no more than max_tokens
    2. tx can no long be executed after deadline

    :param ong_bought: Amount of ong converted from some unknown amount of tokens
    :param max_tokens:  Maximum amount of tokens that will be sold to obtain ong_bought amount of ong
    :param deadline: Time after which this tx can no longer be executed
    :param invoker: Account address who wishes to convert some amount of tokens (no more than max_tokens) to ong_bought amount of ong
    :return: Amount of tokens invoker should sell to acquire ong_bought amount of ong
    """
    return _tokenToOngOutput(ong_bought, max_tokens, deadline, invoker, invoker)

def tokenToOngTransferOutput(ong_bought, max_tokens, deadline, recipient, invoker):
    """
    Convert some tokens to specific ong_bought amount of ong and transfer ong to recipient with conditions
    1. the required amount of tokens equal to ong_bought should be no more than max_tokens
    2. tx can no long be executed after deadline

    :param ong_bought: Amount of ong converted from some unknown amount of tokens
    :param max_tokens:  Maximum amount of tokens that will be sold to obtain ong_bought amount of ong
    :param deadline: Time after which this tx can no longer be executed
    :param recipient: Address that will receive ong
    :param invoker: Account address who wishes to convert some amount of tokens (no more than max_tokens) to ong_bought amount of ong
    :return:
    """
    assert (recipient != GetExecutingScriptHash() and len(recipient) == 20 and recipient != ZERO_ADDRESS)
    return _tokenToOngOutput(ong_bought, max_tokens, deadline, invoker, recipient)

def _tokenToTokenInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, buyer, recipient, exchange_addr):
    # Check the signature of buyer
    assert (CheckWitness(buyer))
    # Legal check
    assert (deadline >= GetTime() and tokens_sold > 0 and min_tokens_bought > 0 and min_ong_bought > 0)
    self = GetExecutingScriptHash()
    assert (exchange_addr != self and exchange_addr != ZERO_ADDRESS and len(exchange_addr) == 20)
    tokenHash = tokenAddress()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    ongBought = _getInputPrice(tokens_sold, tokenReserve, ongReserve)
    # Make sure tokens_sold amount of tokenHash can be exchanged for at least min_ong_bought amount of native asset
    assert (ongBought >= min_ong_bought)
    # Transfer tokens_sold amount of tokenHash to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokens_sold]))
    # Invoke another exchange contract to sell ongBought amount of native asset and buy at least
    # min_tokens_bought amount of another token and transfer the bought token to recipient directly
    tokensBought = DynamicAppCall(exchange_addr, OngToTokenTransferInput_MethodName, [min_tokens_bought, deadline, recipient, self, ongBought])
    assert (tokensBought > 0)
    # Fire event
    OngPurchaseEvent(buyer, tokens_sold, ongBought)
    return

def tokenToTokenSwapInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, token_addr, invoker):
    """
    Convert token1 within current exchange to another token2 of token_addr and transfer token_addr to recipient with conditions:
    1. tokens_sold amount of token1 will be sold out
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the bought amount of token2 should be no less than min_tokens_bought
    4. the converted ong amount from selling tokens_sold amount of token1 should be no less than min_ong_bought
        min_ong_bought means how many ong at minimum we expect to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_sold: Amount of token sold
    :param min_tokens_bought: Minimum tokens of token_addr purchased
    :param min_ong_bought: Minimum ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param token_addr: Address of token being purchased
    :param invoker: Account address expecting to convert his tokens to token_addr
    :return: Amount of tokens (token_addr) bought
    """
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, invoker, invoker, exchangeAddr)

def tokenToTokenTransferInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, recipient, token_addr, invoker):
    """
    Convert tokens_sold amount of token1 within current exchange to another token2 of token_addr and transfer token_addr to recipient with conditions:
    1. tokens_sold amount of token1 will be sold out
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the bought amount of token2 should be no less than min_tokens_bought
    4. the converted ong amount from selling tokens_sold amount of token1 should be no less than min_ong_bought
        min_ong_bought means how many ong at minimum we expect to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_sold: Amount of token sold
    :param min_tokens_bought: Minimum tokens of token_addr purchased
    :param min_ong_bought: Minimum ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param recipient: Address that receives output token_addr
    :param token_addr: Address of token being purchased
    ::param invoker: Account address expecting to convert his tokens to token_addr
    :return: Amount of tokens (token_addr) bought
    """
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, invoker, recipient, exchangeAddr)


def _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, buyer, recipient, exchange_addr):
    # Check signature of buyer
    assert (CheckWitness(buyer))
    # Legal check
    assert (deadline >= GetTime() and tokens_bought > 0 and max_ong_sold > 0)
    self = GetExecutingScriptHash()
    assert (exchange_addr != self and exchange_addr != ZERO_ADDRESS and len(exchange_addr) == 20)
    # Calculate how much native asset should we provide to buy tokens_bought amount token in exchange_addr platform
    ongBought = DynamicAppCall(exchange_addr, GetNaToTokenOutputPrice_MethodName, [tokens_bought])
    tokenHash = tokenAddress()
    # Obtain current token and native asset balance of current contract
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how much tokens we have to sell to obtain ongBought amount of native asset in current exchange
    tokensSold = _getOutputPrice(ongBought, tokenReserve, ongReserve)
    # Condition check
    # 1. The tokens sold to obtain tokens_bought amount of another token is at most max_token_sold
    # 2. To acquire tokens_bought amount of another token, we expect to provide at most max_ong_sold amount of native asset
    assert (max_tokens_sold >= tokensSold and max_ong_sold >= ongBought)
    # Transfer tokensSold amount of token to current contract
    assert (DynamicAppCall(tokenHash, TransferFrom_MethodName, [self, buyer, self, tokensSold]))
    # Invoke another exchange to convert ongBought amount native asset to tokens_bought amount of another token
    assert (DynamicAppCall(exchange_addr, OngToTokenTransferOutput_MethodName, [tokens_bought, deadline, recipient, self, ongBought]))
    return tokensSold


def tokenToTokenSwapOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, token_addr, invoker):
    """
    Convert some token1 within current exchange to tokens_bought amount of another token2 of token_addr and transfer token_addr to invoker with conditions:
    1. tokens_bought amount of token2 should be bought
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the sold amount of token1 should be no more than max_token_sold
    4. the converted ong amount from purchasing tokens_bought amount of token2 should be no more than max_ong_sold
        max_ong_sold means how many ong at maximum from selling token1 we expect to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_bought: Amount of tokens (token_addr) bought
    :param max_tokens_sold: Maximum tokens (within current exchange) sold
    :param max_ong_sold: Maximum Ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param token_addr: Address of token being purchased
    :param invoker: Account address expecting to convert his tokens to token_addr
    :return: Amount of tokens (within current exchange) sold
    """
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, invoker, invoker, exchangeAddr)

def tokenToTokenTransferOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, recipient, token_addr, invoker):
    """
    Convert some token1 within current exchange to tokens_bought amount of another token2 of token_addr and transfer token_addr to recipient with conditions:
    1. tokens_bought amount of token2 should be bought
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the sold amount of token1 should be no more than max_token_sold
    4. the converted ong amount from purchasing tokens_bought amount of token2 should be no more than max_ong_sold
        max_ong_sold means how many ong at maximum from selling token1 we expect to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_bought: Amount of tokens (token_addr) bought
    :param max_tokens_sold: Maximum tokens (within current exchange) sold
    :param max_ong_sold: Maximum Ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param recipient: Address that receives output token_addr
    :param token_addr: Address of token being purchased
    :param invoker: Account address expecting to convert his tokens to token_addr
    :return: Amount of tokens (within current exchange) sold
    """
    exchangeAddr = DynamicAppCall(factoryAddress(), GetExchange_MethodName, [token_addr])
    return _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, invoker, recipient, exchangeAddr)


def tokenToExchangeSwapInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, exchange_addr, invoker):
    """
    Convert token1 within current exchange to another token2 supported within exchange_addr and transfer token2 to invoker with conditions:
    1. tokens_sold amount of token1 will be sold out
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the bought amount of token2 should be no less than min_tokens_bought
    4. the converted ong amount from selling tokens_sold amount of token1 should be no less than min_ong_bought
        min_ong_bought means how many ong at minimum we expect to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_sold: Amount of token sold
    :param min_tokens_bought: Minimum tokens of token_addr purchased
    :param min_ong_bought: Minimum ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param exchange_addr: Address of exchange for the token being purchased
    :param invoker: Account address expecting to convert his tokens to exchange_addr.token
    :return: Amount of tokens (exchange_addr.token) bought
    """
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, invoker, invoker, exchange_addr)

def tokenToExchangeTransferInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, recipient, exchange_addr, invoker):
    """
    Convert token1 within current exchange to another token2 supported within exchange_addr and transfer token2 to recipient with conditions:
    1. tokens_sold amount of token1 will be sold out
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the bought amount of token2 should be no less than min_tokens_bought
    4. the converted ong amount from selling tokens_sold amount of token1 should be no less than min_ong_bought
        min_ong_bought means how many ong at minimum user expects to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_sold: Amount of token sold
    :param min_tokens_bought: Minimum tokens of token_addr purchased
    :param min_ong_bought: Minimum ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param recipient: Address that receive output token_addr
    :param exchange_addr: Address of exchange for the token being purchased
    :param invoker: Account address expecting to convert his tokens to exchange_addr.token
    :return: Amount of tokens (exchange_addr.token) bought
    """
    assert (recipient != GetExecutingScriptHash())
    return _tokenToTokenInput(tokens_sold, min_tokens_bought, min_ong_bought, deadline, invoker, recipient, exchange_addr)


def tokenToExchangeSwapOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, exchange_addr, invoker):
    """
    Convert some token1 within current exchange to tokens_bought of another token2 supported within exchange_addr
    and transfer tokens_bought amount of token2 to invoker with conditions:
    1. user expects to purchase and acquire tokens_bought amount of token2
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the sold amount of token1 should be no more than max_tokens_sold
    4. the converted ong amount from purchasing tokens_sold amount of token2 should be no more than max_ong_sold
        max_ong_sold means how many ong at maximum user bears to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_bought: Exact amount of tokens (exchange_addr.token) bought user expects to purchase
    :param max_tokens_sold: Maximum tokens (self.token) sold
    :param max_ong_sold: Maximum ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param exchange_addr: Address of exchange for the token being purchased
    :param invoker: Account address expecting to convert his tokens to exchange_addr.token
    :return: Amount of tokens (self.token) sold
    """
    return _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, invoker, invoker, exchange_addr)

def tokenToExchangeTransferOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, recipient, exchange_addr, invoker):
    """
    Convert some token1 within current exchange to tokens_bought of another token2 supported within exchange_addr
    and transfer tokens_bought amount of token2 to invoker with conditions:
    1. user expects to purchase and acquire tokens_bought amount of token2
    2. both exchanges supporting token1 and token2 were created by the same factory
    3. the sold amount of token1 should be no more than max_tokens_sold
    4. the converted ong amount from purchasing tokens_sold amount of token2 should be no more than max_ong_sold
        max_ong_sold means how many ong at maximum user bears to use to purchase token2
    5. tx can no long be executed after deadline

    :param tokens_bought: Exact amount of tokens (exchange_addr.token) bought user expects to purchase
    :param max_tokens_sold: Maximum tokens (self.token) sold
    :param max_ong_sold: Maximum ong purchased as intermediary
    :param deadline: Time after which this tx can no longer be executed
    :param recipient: The address receives tokens_bought amount of exchange_addr.token
    :param exchange_addr: Address of exchange for the token being purchased
    :param invoker: Account address expecting to convert his tokens to exchange_addr.token
    :return: Amount of tokens (self.token) sold
    """
    assert (recipient != GetExecutingScriptHash())
    return _tokenToTokenOutput(tokens_bought, max_tokens_sold, max_ong_sold, deadline, invoker, recipient, exchange_addr)


def getOngToTokenInputPrice(ong_sold):
    """
    Calculate how many tokens user can get if he provides an exact input ong
    :param ong_sold: Amount of ong sold
    :return: Amount of tokens that can be bought with ong_sold amount of ong
    """
    assert (ong_sold > 0)
    # Obtain the token and native asset balance of contract
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how many token we will get if we provide ong_sold amount of native asset
    return _getInputPrice(ong_sold, ongReserve, tokenReserve)

def getOngToTokenOutputPrice(tokens_bought):
    """
    Calculate how many ong user should provide to get tokens_bought amount of tokens
    :param tokens_bought: Amount of tokens bought
    :return: Amount of ong needed to buy output tokens
    """
    assert (tokens_bought > 0)
    # Obtain the token and native asset balance of contract
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    # Calculate how many native asset we have to pay to acquire tokens_bought amount of tokens
    return _getOutputPrice(tokens_bought, ongReserve, tokenReserve)

def getTokenToOngInputPrice(tokens_sold):
    """
    Calculate how many ong user can get if he sells tokens_sold amount of tokens
    :param tokens_sold: Amount of tokens sold
    :return: Amount of ong that can be used to purchase tokens_sold amount of tokens
    """
    assert (tokens_sold > 0)
    # Obtain the token and native asset balance of contract
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    return _getInputPrice(tokens_sold, tokenReserve, ongReserve)

def getTokenToOngOutputPrice(ong_bought):
    """
    Calculate how many tokens use should provide to get ong_bought amount of ong
    :param ong_bought: Amount of output ong
    :return: Amount of tokens needed to buy output ong
    """
    assert (ong_bought > 0)
    # Obtain the token and native asset balance of contract
    tokenHash = tokenAddress()
    self = GetExecutingScriptHash()
    tokenReserve = DynamicAppCall(tokenHash, BalanceOf_MethodName, [self])
    ongReserve = Invoke(0, NATIVE_ASSET_ADDRESS, BalanceOf_MethodName, state(self))
    return _getOutputPrice(ong_bought, tokenReserve, ongReserve)


def _getInputPrice(input_amount, input_reserve, output_reserve):
    """
    Suppose, we want to use input_amount of token1 to exchange for token2 considering current contract balances:
    token1 -> input_reserve, token2 -> output_reserve, and this function calculates how many token2 we will
    get.
    1. Parameter definition: input_amount -> ia, input_reserve -> ir, output_reserve -> or, returned value -> oa
    2. The logic gives us the constrain:
            ir * or = [ir + ia * (1 - fee)] * (or - oa)
    3. Conclusion:
            oa = ia * (1 - fee) * or / [ir + ia * (1 - fee)]
    :param input_amount:
    :param input_reserve:
    :param output_reserve:
    :return:
    """
    assert (input_reserve > 0 and output_reserve > 0)
    inputAmountWithFee = input_amount * 9975
    numerator = inputAmountWithFee * output_reserve
    denominator = input_reserve * 10000 + inputAmountWithFee
    return numerator / denominator

def _getOutputPrice(output_amount, input_reserve, output_reserve):
    """
    Suppose, we want to obtain output_amount of token2 considering current contract balances:
    token1 -> input_reserve, token2 -> output_reserve, and this function calculates how many
    token1 we need to provide for exchanging in order to get exact output_amount of token2 finally.
    1. Parameter definition: output_amount -> oa, input_reserve -> ir, output_reserve -> or, returned value -> ia
    2. The logic gives us the constrain:
            ir * or = [ir + ia * (1 - fee)] * (or - oa)
    3. Conclusion:
            ia = ir * oa / [(or - oa) * (1 - fee)] + 1
    :param input_amount:
    :param input_reserve:
    :param output_reserve:
    :return:
    """
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


def transfer(from_acct, to_acct, amount):
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
        Put(GetContext(), fromKey, fromBalance - amount)
    toKey = concat(BALANCE_PREFIX, to_acct)
    toBalance = Get(GetContext(), toKey)
    Put(GetContext(),toKey, toBalance + amount)

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


def transferFrom(spender, from_acct, to_acct, amount):
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


def approve(owner, spender, amount):
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


def allowance(owner, spender):
    """
    check how many token the spender is allowed to spend from owner account
    :param owner: token owner
    :param spender:  token spender
    :return: the allowed amount of tokens
    """
    return Get(GetContext(), concat(concat(APPROVE_PREFIX, owner), spender))