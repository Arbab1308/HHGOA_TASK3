import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Tuple, Optional
from web3 import Web3
from eth_tester import EthereumTester

logger = logging.getLogger(__name__)

class BlockchainVerifier:
    """
    Handles uploading verification data to a blockchain and verifying it later.
    By default, uses an in-memory Ethereum blockchain (eth-tester) for zero-setup
    execution during the hackathon, but can be configured for public testnets.
    """
    def __init__(self, use_local_chain: bool = True):
        logger.info(f"Initializing BlockchainVerifier (local_chain={use_local_chain})...")
        self.use_local_chain = use_local_chain
        self.chain_name = "Local Simulated Chain (eth-tester)" if use_local_chain else "Ethereum Sepolia"
        
        if use_local_chain:
            # Initialize in-memory blockchain for instant testing
            self.eth_tester = EthereumTester()
            self.w3 = Web3(Web3.EthereumTesterProvider(self.eth_tester))
            self.account = self.w3.eth.accounts[0]
        else:
            # Connect to a real testnet (requires environment variables)
            infura_url = os.getenv("INFURA_URL", "https://sepolia.infura.io/v3/YOUR-PROJECT-ID")
            self.w3 = Web3(Web3.HTTPProvider(infura_url))
            private_key = os.getenv("PRIVATE_KEY")
            if private_key:
                self.account = self.w3.eth.account.from_key(private_key).address
            else:
                logger.warning("No PRIVATE_KEY provided in env, blockchain uploads will fail.")
                self.account = None

        if self.w3.is_connected():
            logger.info(f"Successfully connected to {self.chain_name}")
        else:
            logger.error(f"Failed to connect to {self.chain_name}")

    def setup_account(self):
        """Validates the account balance and setup."""
        if not self.account:
            return
            
        balance = self.w3.eth.get_balance(self.account)
        logger.info(f"Using account: {self.account}")
        logger.info(f"Balance: {self.w3.from_wei(balance, 'ether')} ETH")

    def _create_data_hash(self, face_encoding_sig: str, post_metadata: Dict) -> str:
        """Creates a composite hash of the face and the discovered post."""
        payload = {
            "face_sig": face_encoding_sig,
            "post_platform": post_metadata.get("source_platform"),
            "post_author": post_metadata.get("author_id"),
            "post_hash": post_metadata.get("content_hash"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    def upload_to_blockchain(self, face_encoding_sig: str, social_post: Dict, post_metadata: Dict) -> Tuple[str, Dict]:
        """
        Embeds the composite hash into a blockchain transaction to create a permanent,
        tamper-evident record of the discovery.
        """
        try:
            # Generate the unique hash for this verification event
            data_hash = self._create_data_hash(face_encoding_sig, post_metadata)
            
            # Prepare transaction payload (Hex representation of the hash)
            tx_data = self.w3.to_hex(text=data_hash)
            
            tx = {
                'to': self.account,  # Sending to self just to embed data on-chain
                'value': 0,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account),
                'data': tx_data
            }
            
            if self.use_local_chain:
                # With eth-tester, we can just send the transaction
                tx_hash = self.w3.eth.send_transaction({
                    'from': self.account,
                    **tx
                })
                tx_hash_hex = self.w3.to_hex(tx_hash)
            else:
                # For real networks, we sign it with the private key
                private_key = os.getenv("PRIVATE_KEY")
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = self.w3.to_hex(tx_hash)
                
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            blockchain_record = {
                "transaction_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "data_hash": data_hash,
                "face_signature": face_encoding_sig,
                "verified_post_id": social_post.get("post_id"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            return tx_hash_hex, blockchain_record
            
        except Exception as e:
            logger.error(f"Blockchain upload failed: {e}")
            raise

    def verify_data_on_blockchain(self, data_hash: str) -> Tuple[bool, Dict]:
        """
        Verifies that a specific data hash exists on the blockchain by scanning
        recent transactions (or in a real scenario, retrieving by tx hash).
        """
        try:
            # Look through recent blocks to find our data hash
            found = False
            tx_hash_found = None
            
            current_block_num = self.w3.eth.block_number
            start_block = max(0, current_block_num - 5)
            
            for block_num in range(current_block_num, start_block - 1, -1):
                block = self.w3.eth.get_block(block_num)
                for tx_hash in block['transactions']:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    
                    # Check if our data hash was embedded in this transaction's input data
                    try:
                        tx_input_text = self.w3.to_text(primitive=tx['input'])
                        if data_hash in tx_input_text:
                            found = True
                            tx_hash_found = self.w3.to_hex(tx_hash)
                            break
                    except:
                        continue
                if found:
                    break
                    
            details = {
                "searched_hash": data_hash,
                "blocks_checked": f"{start_block} to {current_block_num}",
                "found_on_chain": found,
                "transaction_hash": tx_hash_found,
                "verification_time": datetime.utcnow().isoformat() + "Z"
            }
            
            return found, details
            
        except Exception as e:
            logger.error(f"Error verifying on blockchain: {e}")
            return False, {"error": str(e)}

    def get_verification_certificate(self, data_hash: str, blockchain_record: Dict) -> Dict:
        """Generates a printable JSON certificate of authenticity."""
        return {
            "certificate_id": f"CERT-{data_hash[:8].upper()}",
            "issuer": "HH Goa 2026 Verification Node",
            "issue_date": datetime.utcnow().isoformat() + "Z",
            "blockchain": self.chain_name,
            "verification_record": blockchain_record,
            "status": "VALID",
            "authenticity_seal": hashlib.sha256(f"VALID_{data_hash}".encode()).hexdigest()
        }

    def save_blockchain_record(self, record: Dict, file_path: str):
        with open(file_path, 'w') as f:
            json.dump(record, f, indent=2)
            
    def save_certificate(self, cert: Dict, file_path: str):
        with open(file_path, 'w') as f:
            json.dump(cert, f, indent=2)
