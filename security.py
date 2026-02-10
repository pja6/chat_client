import encrypt

class Security_Manager:
    def __init__(self, username):
        self.username = username
        self.rsa_pub, self.rsa_priv = encrypt.make_rsa_key(2048)
        self.dh_private = None
        self.dh_public = None
        # username|secret
        self.shared_secrets = {}
        
    
    # gen keys and returns formatted INIT string
    def create_dh_packet(self, target_user):
        self.dh_private = encrypt.gen_priv_key(encrypt.MOD1536_P)
        self.dh_public = encrypt.gen_pub_val(encrypt.MOD1536_P, encrypt.MOD1536_G, self.dh_private)
        
   
        #prep for toy rsa signature
        send_sig = pow(self.dh_public, self.rsa_priv[1], self.rsa_priv[0])
        
        # 6 sections: [0]Target | [1]Type | [2]DH_Pub | [3]RSA_n | [4]RSA_e | [5]Sig
        return f"{target_user}|DH_INIT|{self.dh_public}|{self.rsa_pub[0]}|{self.rsa_pub[1]}|{send_sig}"
    
    
    # verifies an INIT and returns a response packet / computes secret
    def verify_respond(self, sender, s_dh_pub, s_rsa_n, s_rsa_e, s_sig):
        print(f"[SEC_MGR] verify_respond called for sender: {sender}")
        print(f"[SEC_MGR] s_dh_pub length: {len(s_dh_pub)}")
        print(f"[SEC_MGR] s_sig: {s_sig[:50]}...")
        
        try:
            decrypted_sig = encrypt.dcipher(int(s_sig), int(s_rsa_e), int(s_rsa_n))
            
            #added a lot of debugging - nice that it shows up on terminal now though
            if str(decrypted_sig) == s_dh_pub:
                print(f"[SEC_MGR] Signature verified! Computing shared secret...")
                self.dh_private = encrypt.gen_priv_key(encrypt.MOD1536_P)
                self.dh_public = encrypt.gen_pub_val(encrypt.MOD1536_P, encrypt.MOD1536_G, self.dh_private)
                
                # Compute secret
                self.shared_secrets[sender] = encrypt.gen_sym_key(int(s_dh_pub), self.dh_private, encrypt.MOD1536_P)
                print(f"[SEC_MGR] Shared secret computed: {str(self.shared_secrets[sender])[:50]}...")
                
                # Respond
                response_sig = pow(self.dh_public, self.rsa_priv[1], self.rsa_priv[0])
                
                response = f"{sender}|DH_RESPONSE|{self.dh_public}|{self.rsa_pub[0]}|{self.rsa_pub[1]}|{response_sig}"
                print(f"[SEC_MGR] Sending DH_RESPONSE back to {sender}")
                print(f"[SEC_MGR] Response length: {len(response)}")
                
                return response
            else:
                print(f"[SEC_MGR] Signature verification FAILED!")
                return None
        except Exception as e:
            print(f"[SEC_MGR] Exception in verify_respond: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    
    # verifies response / computes secret    
    def finalize_secret(self, sender, s_dh_pub, s_rsa_n, s_rsa_e, s_sig):
        decrypted_sig = pow(int(s_sig), int(s_rsa_e), int(s_rsa_n))
        
        if decrypted_sig == int(s_dh_pub):
            
            self.shared_secrets[sender] = encrypt.gen_sym_key(int(s_dh_pub), self.dh_private, encrypt.MOD1536_P)
            
            return True
        return False
    
    
def main():
    print("AES block size:", AES.block_size)


if __name__=="__main__":
    main()