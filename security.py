import encrypt

class Security_Manager:
    def __init__(self, username):
        self.username = username
        self.rsa_pub, self.rsa_priv = encrypt.make_key(1024)
        self.dh_private = None
        self.dh_public = None
        # username|secret
        self.shared_secrets = {}
        
    
    # gen keys and returns formatted INIT string
    def create_dh_packet(self, target_user):
        self.dh_private = encrypt.gen_priv_key(encrypt.MOD3072_P)
        self.dh_public = encrypt.gen_pub_val(encrypt.MOD3072_P, encrypt.MOD3072_G, self.dh_private)
        
        #prep for toy rsa signature
        dh_bytes = str(self.dh_public).encode()
        send_sig = encrypt.cipher(dh_bytes, self.rsa_priv[1], self.rsa_priv[0])
        
        return f"DH_INIT|{target_user}|{self.dh_public}|{self.rsa_pub[0]}|{self.rsa_pub[1]}|{send_sig}"
    
    
    # verifies an INIT and returns a response packet / computes secret
    def verify_respond(self, sender, s_dh_pub, s_rsa_n, s_rsa_e, s_sig):
        decrypted_sig = encrypt.dcipher(int(s_sig), int(s_rsa_e), int(s_rsa_n))
        
        #if the public val is legit, start computing secret
        if str(decrypted_sig) == s_dh_pub:
            self.dh_private = encrypt.gen_priv_key(encrypt.MOD3072_P)
            self.dh_public = encrypt.gen_pub_val(encrypt.MOD3072_P, encrypt.MOD3072_G, self.dh_private)
            
            #compute secret
            self.shared_secrets[sender] = encrypt.gen_sym_key(int(s_dh_pub), self.dh_private, encrypt.MOD3072_P)
            
            
            #respond
            dh_bytes = str(self.dh_public).encode()
            response_sig = encrypt.cipher(dh_bytes, self.rsa_priv[1], self.rsa_priv[0])
            
            return f"DH_RESPONSE|{sender}|{self.dh_public}|{self.rsa_pub[0]}|{self.rsa_pub[1]}|{response_sig}"
        
    
    # verifies response / computes secret    
    def finalize_secret(self, sender, s_dh_pub, s_rsa_n, s_rsa_e, s_sig):
        decrypted_sig = encrypt.dcipher(int(s_sig), int(s_rsa_e), int(s_rsa_n))
        
        if str(decrypted_sig) == s_dh_pub:
            
            self.shared_secrets[sender] = encrypt.gen_sym_key(int(s_dh_pub), self.dh_private, encrypt.MOD3072_P)
            
            return True
        return False