import encrypt
import json
import base64
from collections import OrderedDict

class Security_Manager:
    def __init__(self, username):
        self.username = username
        self.rsa_pub, self.rsa_priv = encrypt.make_rsa_key(2048)
        self.dh_private = None
        self.dh_public = None
        # username|secret
        self.shared_secrets = {}
        self.cached_keys=OrderedDict()
        self.key_count=1  #key rotation/cache mechanism
        self.recv_counters = {}   # sender -> expected msg_num
        self.send_counters = {}   # target -> next msg_num to send

# ============================   DH Exchange ====================================== 
    
    # gen keys and returns formatted INIT string
    def create_dh_packet(self, target_user):
        self.dh_private = encrypt.gen_priv_key(encrypt.MOD1536_P)
        self.dh_public = encrypt.gen_pub_val(encrypt.MOD1536_P, encrypt.MOD1536_G, self.dh_private)
        
   
        #prep for toy rsa signature
        send_sig = pow(self.dh_public, self.rsa_priv[1], self.rsa_priv[0])
        
        #updated protocol
        packet = {
            "sender": self.username,
            "target": target_user,
            "msg_type": "DH_INIT",
            "dh_public": self.dh_public,
            "rsa_n": self.rsa_pub[0],
            "rsa_e": self.rsa_pub[1],
            "signature": send_sig
        }
        
        return json.dumps(packet)
    
    # verifies an INIT and returns a response packet / computes secret
    def verify_respond(self, packet_data):
        try:
            sender = packet_data["sender"]
            s_dh_pub = packet_data["dh_public"]
            s_rsa_n = packet_data["rsa_n"]
            s_rsa_e = packet_data["rsa_e"]
            s_sig = packet_data["signature"]
            
            
            print(f"[SEC_MGR] verify_respond called for sender: {sender}")
            #print(f"[SEC_MGR] s_dh_pub length: {len(s_dh_pub)}")
            #print(f"[SEC_MGR] s_sig: {s_sig[:50]}...")
        
            decrypted_sig = encrypt.dcipher(int(s_sig), int(s_rsa_e), int(s_rsa_n))
            
            #added a lot of debugging - nice that it shows up on terminal now though
            if decrypted_sig == s_dh_pub:
                print(f"[SEC_MGR] Signature verified! Computing shared secret...")
                
                #generating dh key pair
                self.dh_private = encrypt.gen_priv_key(encrypt.MOD1536_P)
                self.dh_public = encrypt.gen_pub_val(encrypt.MOD1536_P, encrypt.MOD1536_G, self.dh_private)
                
                # Compute secret
                self.shared_secrets[sender] = encrypt.gen_sym_key(int(s_dh_pub), self.dh_private, encrypt.MOD1536_P)
                print(f"[SEC_MGR] Bob's shared secret with {sender}: {str(self.shared_secrets[sender])[:50]}...")

                print(f"[SEC_MGR] Shared secret computed: {str(self.shared_secrets[sender])[:50]}...")
                
                # sign 
                response_sig = pow(self.dh_public, self.rsa_priv[1], self.rsa_priv[0])
                
                response = {
                    "sender": self.username,
                    "target": sender,
                    "msg_type": "DH_RESPONSE",
                    "dh_public": self.dh_public,
                    "rsa_n": self.rsa_pub[0],
                    "rsa_e": self.rsa_pub[1],
                    "signature": response_sig
                }
                print(f"[SEC_MGR] Sending DH_RESPONSE back to {sender}")
                #print(f"[SEC_MGR] Response length: {len(response)}")
                
                return json.dumps(response)
            else:
                print(f"[SEC_MGR] Signature verification FAILED!")
                return None
            
        except Exception as e:
            print(f"[SEC_MGR] Exception in verify_respond: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    
    # verifies response / computes secret    
    def finalize_secret(self, packet_data):
        
        try:
            sender = packet_data["sender"]
            s_dh_pub = packet_data["dh_public"]
            s_rsa_n = packet_data["rsa_n"]
            s_rsa_e = packet_data["rsa_e"]
            s_sig = packet_data["signature"]
            
            decrypted_sig = pow(int(s_sig), int(s_rsa_e), int(s_rsa_n))
        
            if decrypted_sig == int(s_dh_pub):
                
                self.shared_secrets[sender] = encrypt.gen_sym_key(int(s_dh_pub), self.dh_private, encrypt.MOD1536_P)
                print(f"[SEC_MGR] Alice's shared secret with {sender}: {str(self.shared_secrets[sender])[:50]}...")

                print(f"[SEC_MGR] Shared secret established with {sender}")
                return True
            
            return False
        except Exception as e:
            print(f"[SEC_MGR] Exception in finalize_secret: {e}")
            return False
        
# ================================================= Encrypt Message ===========================
    def burn_key(self, key):
        if len(self.cached_keys) >=3:
            burned_key=self.cached_keys.popitem(last=False)
            print(f"[SEC_MGR] expired key: {burned_key}")
            
        #print(f"[SEC_MGR] burn_key called. Before: {self.key_count}, keys: {list(self.cached_keys.keys())}")
        self.cached_keys[self.key_count]=key
        self.key_count+=1

        print(f"[SEC_MGR] After: {self.key_count}, keys: {list(self.cached_keys.keys())}")

    def encrypt_message(self, packet_data):
        try:
           sender = packet_data["sender"]
           target = packet_data["target"]
           msg_type  = packet_data["msg_type"]
           content = packet_data["content"]
           
           
               
           if target not in self.shared_secrets:
                print(f"[SEC_MGR] No shared secret for {target}")
                return False
           
           if target not in self.send_counters:
                self.send_counters[target] = 1
        
           msg_num=self.send_counters[target]
            
           print(f"[DEBUG] Using shared secret (first 50 chars): {str(self.shared_secrets[target])[:50]}...")
           cipher_text, nonce, mac =encrypt.encrypt_message(self.shared_secrets[target], content)

           self.send_counters[target] += 1

           encrypted_packet={
               "sender": sender,
               "target": target,
               "msg_type": "SECURE_MESSAGE",
               "content": base64.b64encode(cipher_text).decode('utf-8'),
               "c_nonce": base64.b64encode(nonce).decode('utf-8'),
               "mac":base64.b64encode(mac).decode('utf-8'),
               "msg_num": msg_num,
               "encrypted": True
           }

        except Exception as e:
            print(f"[SEC_MGR] Exception in encrypt_message: {e}")
            return False
        
        return encrypted_packet

    def decrypt_message(self, encrypt_data):
        print(f"[SEC_MGR] Attempting to decrypt...")
        try:
            sender = encrypt_data["sender"]
            target = encrypt_data["target"]
            mac = encrypt_data["mac"]
            content = encrypt_data["content"]
            c_nonce = encrypt_data["c_nonce"]
            msg_num=encrypt_data["msg_num"]
            
            
            if sender not in self.recv_counters:
                self.recv_counters[sender] = 1
                
            expected = self.recv_counters[sender]

            if msg_num == expected:
                print(f"[DEBUG] Using shared secret (first 50 chars): {str(self.shared_secrets[sender])[:50]}...") 

                content_bytes = base64.b64decode(content)
                nonce_bytes = base64.b64decode(c_nonce)
                mac_bytes = base64.b64decode(mac)
                plain_txt, key = encrypt.decrypt_message(self.shared_secrets[sender], content_bytes, nonce_bytes, mac_bytes)
                
                print(f"[DEBUG] msg_num: {msg_num}, key_count: {self.key_count}")
                
                self.recv_counters[sender] += 1
                self.burn_key(key)

                decrypted_packet={
                    "sender": sender,
                    "target": target,
                    "msg_type": "MESSAGE",
                    "content": plain_txt,
                    "msg_num": msg_num,
                    "encrypted": False
                }
            else: 
                decrypted_packet={
                    "msg_type": "SYSTEM",
                    "msg_num": 1,
                    "content": "Key/Msg Mismatch - resetting"
                }
                self.key_count=1
        except Exception as e:
            print(f"[SEC_MGR] Exception in decrypt_message: {e}")
            return False
        
        return decrypted_packet
    
def main():
    print("AES block size:", AES.block_size)


if __name__=="__main__":
    main()