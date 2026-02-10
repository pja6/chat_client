#!/usr/bin/python3
# Retrieved from: http://en.literateprograms.org/Miller-Rabin_primality_test_(Python)?oldid=17104

from Crypto.Cipher import AES
import math
import random, sys, os

#since using standard public numbers, keeping as constants
# actually 1536-bit MODP Group - had to change it, didnt update name
MOD1536_P=0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF

MOD1536_G= 2

#==================================== RSA =======================================
def miller_rabin_pass(a, s, d, n):
    a_to_power = pow(a, d, n)
    if a_to_power == 1:
        return True
    for i in range(s-1):
        if a_to_power == n - 1:
            return True
        a_to_power = (a_to_power * a_to_power) % n
    return a_to_power == n - 1


def miller_rabin(n):
    d = n - 1
    s = 0
    while d % 2 == 0:
        d >>= 1
        s += 1
    for repeat in range(20):
        a = 0
        while a == 0:
            a = random.randrange(n)
        if not miller_rabin_pass(a, s, d, n):
            return False
    return True

def test_num(num):
    n = int(num)
    return (miller_rabin(n) and "PRIME" or "COMPOSITE")

def gen_prime(nbits):
        while True:
            p = random.getrandbits(nbits)
            p |= 2**nbits | 1
            if miller_rabin(p):
                return p


def cipher(m,e,n):
    i = int.from_bytes(m)
    return pow(i,e,n)

def dcipher(c,d,n):

    return pow(c,d,n)

def make_rsa_key(bit_len):
    e = 65537
    p= gen_prime(bit_len)
    q= gen_prime(bit_len)

    n= p*q
    lamn = math.lcm((p-1),(q-1))
    d=modinv(e, lamn)

    # compute n and d
    # (n,e) is your public key
    # (n,d) is your private key
    # use 65537 as e


    return((n,e),(n,d))

def egcd(a, b):
    x,y, u,v = 0,1, 1,0
    while a != 0:
        q,r = b//a,b%a; m,n = x-u*q,y-v*q
        b,a, x,y, u,v = a,r, u,v, m,n
    return b, x, y

"""
function to find modular multiplicative inverse in RSA
must give e and totient
stole this code too :)
"""
def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        return None  # modular inverse does not exist
    else:
        return x % m

#======================================== Diffie-Helman Exc. ============================
"""" at this point just orchestration, each client doing things independently, will just use functions
def diffie_hellman():
    
    A_key = gen_priv_key(MOD3072_P)
    B_key = gen_priv_key(MOD3072_P)
    
    A_val = gen_pub_val(MOD3072_P, MOD3072_G, A_key)
    B_val = gen_pub_val(MOD3072_P, MOD3072_G, B_key)
    
    
    kA = gen_sym_key(B_val, A_key, MOD3072_P)
    kB = gen_sym_key(A_val, B_key, MOD3072_P)
    
    return kA,kB
"""


def gen_priv_key(pub_p):
    rand_byte = os.urandom(256)
    priv_key = int.from_bytes(rand_byte, 'big')
    
    #make sure that random num is within range of 2 < private key < p-1 (trivial if less than 2 or = to p-1)
    if priv_key < 2:
        priv_key = 2
    if priv_key >= pub_p:
        priv_key = priv_key % (pub_p - 2) + 2
        
    return priv_key

def gen_pub_val(pub_p, pub_g, priv_p):
    public_val =pow(pub_g, priv_p, pub_p)
     
    return public_val
 
def gen_sym_key(swap_pub_val, priv_key, pub_p):
    shared_secret= pow(swap_pub_val, priv_key, pub_p)
    
    return shared_secret


#====================================== AES STREAM CIPHER ========================

def encrypt_message(shared_secret, plain_text):
    key = shared_secret
    cipher = AES.new(key, AES.MODE_CTR)
    
    nonce = cipher.nonce
    cipher_text, tag = cipher.encrypt_and_digest(plain_text)
    
    return cipher_text, tag, nonce


def decrypt_message(shared_secret, cipher_text, tag, nonce):
    key = shared_secret
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    plain_text = cipher.decrypt(cipher_text)
    
    try: 
        cipher.verify(tag)
        print(f"The message is authentic: {plain_text}")
    except ValueError:
        print("Key incorrect or message corrupted")
    

#This isn't used, was just for testing the RSA code
def main():

    public,private = make_rsa_key(int(sys.argv[1]))

    print("RSA Keys Created:")
    #public key = (n,e)
    print(f"public key is ({public[0]},{public[1]})")

    #private key = (n,d)
    print(f"private key is ({private[0]},{private[1]})")
    

    print('------------------------------------------------------------------------')
    #message to encrypt
    msg = b'This is OnlY a test...message'
    print ("Message to encrypt: ") 
    print(msg)
    #print(int.from_bytes(msg))
    print("\n")

    print('------------------------------------------------------------------------')

    print("Public Encrypt/Private Decrypt")
    #cipher with public key
    x = cipher(msg,public[1],public[0])
    print("Encrypted Message: ")
    print(x)

    #decipher with private key
    y = dcipher(x, private[1], private[0])
    print("Decrypted Message: ")
    print(y.to_bytes(len(msg)))
    print('------------------------------------------------------------------------')

    print("Private Encrypt/Public Decrypt")
    c= cipher(msg, private[1], private[0])
    print("Encrypted Message: ")
    print(c)

    m= dcipher(c, public[1], public[0])
    print("Decrypted Message: ")
    print(m.to_bytes(len(msg)))

if __name__ == "__main__":
    main()