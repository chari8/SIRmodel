
class DecodeTenji:

    def __init__(self, sets):
        self.sets = sets

    def decode(self):
        dhFlg = 0
        sokuFlg = 0
        
        for st in self.tenji2Bin():

            # NULL
            if st == 0:
                print(" ")
                continue
            
            con = st & 0b111
            vowel = st >> 3
            
            dict_v = {0b100:"A", 0b101:"I", 0b110:"U", 0b111:"E", 0b011:"O"}
            dict_v2 = {0b010:"A", 0b011:"U", 0b110:"O", 0b111:"N "}
            dict_c = {0b000:" ", 0b001:"K", 0b101:"S", 0b110:"T", 0b010:"N", 0b011:"H", 0b111:"M", 0b100:"R"}
            toDak = {"K":"G", "S":"Z", "T":"D", "H":"B"}
            toHan = {"H":"P"}
            
            # Exception
            # Dash            
            if vowel == 0b001:
                if con == 0b100:
                    print("--")
                if con == 0:
                    #XTU
                    sokuFlg = 1
            # YAYUYO
            elif vowel == 0b010:
                print("Y")
                print(dict_v2[vowel])
                
            # WAWON or Dak,Han
            elif vowel == 0:
                if con == 0b100:
                    dhFlg = 1
                elif con == 0b001:
                    dhFlg = 2
                else:
                    print("W")
                    print(dict_v2[con])                    
            else:
                # In general

                # Consonant
                if dhFlg == 1:
                    str = toDak[dict_c[con]]
                elif dhFlg == 2:
                    str = toHan[dict_c[con]]
                else:
                    str = dict_c[con]
                print(str)
                if sokuFlg:
                    print(str)
                    
                # Vowel
                print(dict_v[vowel])
                
                # Reset
                dhFlg = 0
                sokuFlg = 0

    def tenji2Bin(self):
        ans = []
        for st in self.sets:
            ans.append(sum(map(lambda n:2**(6-n), st)))
        return ans

hg = DecodeTenji([[2,3,5,6], [4], [1,2,3,6], [], [6], [2,3,5,6], [1,3,6], [1,4,5]])
hg.decode()
