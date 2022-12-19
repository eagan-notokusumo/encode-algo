# import dependencies
from algosdk import account, mnemonic, constants
from algosdk.v2client import algod
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn
from algosdk.future.transaction import *
from algosdk.mnemonic import to_private_key
import json

# function to create initial addresses for transaction
def generate_algorand_keypairs(n):
    addresses = []
    pks = []
    for i in range(n):
        private_key, address = account.generate_account()
        addresses.append(address)
        pks.append(pks)
    # print(addresses)
    # print(pks)
    return pks, addresses

#initialize algod client using testnet
algod_address = "https://testnet-api.algonode.cloud"
algod_client = algod.AlgodClient("", algod_address)
params = algod_client.suggested_params()
# initialiation of addresses for asset transaction examples, make sure there are funds in creator account
# pks, addresses = generate_algorand_keypairs(3)
def initial_funding(pk, sender_address, receiver_address):
    # account_info = algod_client.account_info(address)
    txn = PaymentTxn(
        sender=sender_address,
        sp=params,
        receiver=receiver_address,
        amt=10000,
        close_remainder_to=None,
        note='Hello World'.encode()
    )

    stxn = txn.sign(pk)
    
    # wait for confirmation 
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 4)  
    except Exception as err:
        print(err)
        return

    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
    print("Decoded note: {}".format(base64.b64decode(
        confirmed_txn["txn"]["txn"]["note"]).decode()))

    print("Starting Account balance: {} microAlgos".format(account_info.get('amount')) )
    print("Amount transfered: {} microAlgos".format(txn.amt))    
    print("Fee: {} microAlgos".format(params.fee) ) 

    account_info = algod_client.account_info(receiver_address)
    print("Final Account balance: {} microAlgos".format(account_info.get('amount')) + "\n")

def print_created_asset(algodclient, account, assetid):    
    account_info = algodclient.account_info(account)
    idx = 0;
    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx = idx + 1       
        if (scrutinized_asset['index'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['index']))
            print(json.dumps(my_account_info['params'], indent=4))
            break

def print_asset_holding(algodclient, account, assetid):
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1        
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break

def create_asset(pks, addresses): 
    txn = AssetConfigTxn(
        sender=addresses[0], # address 1 is the creator
        sp=params,
        total=1000,
        default_frozen=False,
        unit_name="LATINUM",
        asset_name="latinum",
        manager=addresses[1], # address 2 is the manager, reserve, freeze, and clawback
        reserve=addresses[1],
        freeze=addresses[1],
        clawback=addresses[1],
        url="https://path/to/my/asset/details", 
        decimals=0)

    # use private key of creator (account 1)
    stxn = txn.sign(pks[0])

    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))   
    except Exception as err:
        print(err)

    # Retrieve Asset ID of confirmed transaction
    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))

    try:
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]
        print_created_asset(algod_client, addresses[0], asset_id)
        print_asset_holding(algod_client, addresses[0], asset_id)
    except Exception as e:
        print(e)


def change_manager(pks, addresses, asset_id):
    # address 2 (the manager) wants to set address1 as the new manager
    txn = AssetConfigTxn(
        sender=addresses[1],
        sp=params,
        index=asset_id,
        manager=addresses[0],
        reserve=addresses[1],
        freeze=addresses[1],
        clawback=addresses[1],
    )

    # signed by current manager
    stxn = txn.sign(pks[1])

    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))
    except Exception as err:
        print(err)
    
    print_created_asset(algod_client, addresses[0], asset_id)

def opt_in(pks, addresses, asset_id):
    # check if assset id is in account 3's holdings prior to opt-in
    account_info = algod_client.account_info(addresses[2])
    holding = None
    idx = 0

    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx += 1
        if (scrutinized_asset['asset-id'] == asset_id):
            holding = True
            break
    
    if not holding:
        # Use the AssetTransferTxn class to transfer assets and opt-in
        txn = AssetTransferTxn(
            sender=addresses[2],
            sp=params,
            receiver=addresses[2],
            amt=0,
            index=asset_id
        )

        stxn = txn.sign(pks[2])

        try:
            txid = algod_client.send_transaction(stxn)
            print("Signed transaction with txID: {}".format(txid))
            # Wait for the transaction to be confirmed
            confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
            print("TXID: ", txid)
            print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))
    
        except Exception as err:
            print(err)
        
        print_asset_holding(algod_client, addresses[2], asset_id)

def transfer_assets(pks, addresses, asset_id):
    # Transfer asset of 10 from account 1 to 3
    txn = AssetConfigTxn(
        sender=addresses[0],
        sp=params,
        receiver=addresses[2],
        amt=10,
        index=asset_id
    )

    stxn = txn.sign(pks[0])

    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))

    except Exception as err:
        print(err)
# The balance should now be 10.
    print_asset_holding(algod_client, addresses[2], asset_id)

def freeze_assets(pks, addresses, asset_id):
    # freeze address freezes account 3's holdings
    txn = AssetFreezeTxn(
        sender=addresses[1],
        sp=params,
        index=asset_id,
        target=addresses[2],
        new_freeze_state=True
    )

    stxn = txn.sign(pks[1])

    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))    
    except Exception as err:
        print(err)
    # The balance should now be 10 with frozen set to true.
    print_asset_holding(algod_client, addresses[2], asset_id)

def revoke_assets(pks, addresses, asset_id):
    # clawback address revokes 10 latinum from account 3 and places it back with account 1
    txn = AssetTransferTxn(
        sender=addresses[1],
        sp=params,
        receiver=addresses[0],
        amt=10,
        index=asset_id,
        revocation_target=addresses[2]
    )

    stxn = txn.sign(pks[1])

    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))      
    except Exception as err:
        print(err)
    # The balance of account 3 should now be 0.
    # account_info = algod_client.account_info(accounts[3]['pk'])
    print("Account 3")
    print_asset_holding(algod_client, addresses[2], asset_id)

    # The balance of account 1 should increase by 10 to 1000.
    print("Account 1")
    print_asset_holding(algod_client, addresses[0], asset_id)

def destroy_asset(pks, addresses, asset_id):
    txn = AssetConfigTxn(
    sender=addresses[0],
    sp=params,
    index=asset_id,
    strict_empty_address_check=False
    )

    # Sign with secret key of creator
    stxn = txn.sign(addresses[0])
    # Send the transaction to the network and retrieve the txid.
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))     
    except Exception as err:
        print(err)

    # Asset was deleted.
    try:
        print("Account 3 must do a transaction for an amount of 0, " )
        print("with a close_assets_to to the creator account, to clear it from its accountholdings")
        print("For Account 1, nothing should print after this as the asset is destroyed on the creator account")
    
        print_asset_holding(algod_client, addresses[0], asset_id)
        print_created_asset(algod_client, addresses[0], asset_id)
        # asset_info = algod_client.asset_info(asset_id)
    except Exception as e:
        print(e)

asset_id = 000000
def all_operations(n):
    pks, addresses = generate_algorand_keypairs(n)
    for i in range(n):
        initial_funding(pks[i],addresses[0],addresses[1:])
    create_asset(pks, addresses)
    change_manager(pks, addresses, asset_id)
    opt_in(pks, addresses, asset_id)
    transfer_assets(pks, addresses, asset_id)
    freeze_assets(pks, addresses, asset_id)
    revoke_assets(pks, addresses, asset_id)
    destroy_asset(pks, addresses, asset_id)

all_operations(3)


    