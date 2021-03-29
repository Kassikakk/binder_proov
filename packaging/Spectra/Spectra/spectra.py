# -*- coding: utf8 -*-
import array
import struct
import time

#versions
DOS1, DOS3, WIN96 = range(3)

class Spc:
    #peab mĆµtlema, kas teha see nn Ć¼he-faili klassiks vĆµi mitte, vist mitte, aga sel juhul tekib kĆ¼simus nt. mis versioon peale jĆ¤Ć¤b vms. ja kui on 
    #8baidised duublid, siis kas jĆ¤Ć¤vad vĆµi mitte. Proovime nii, et uuem versioon vĆµtab pretsedentsi.
    #Siis juba ka, et Ć¤kki vĆµiks valida, missuguseid spektreid tĆ¤psemalt sisse lugeda (list ette?). Kui vst numbriga (kommendiga?) pole, siis None listi?
    #Ja Ć¼ldse - kui see on mingi failiga mitteseotud spektrite kollektsioon, siis nt versiooni vĆµiks ju read/writespc siseasjaks jĆ¤tta?
    
    
    
    def __init__(self, spc = [], start = 0, step = 1, comment = '', date = None ):
        self.spc = spc
        self.start = start
        self.step = step
        self.comment = comment
        
        self.date = date if date is not None else int(time.time()) #kuidas nendega majandada
        #failis loetav on +25200 s e 7 tundi nihkes
        #vast normaalne oleks ka UTC ja ajazooni korrektsioon

        self.dblPrec = False #Kas failis olid / peaksid olema WIN96 versiooni korral 8 - baidised vĆ¤Ć¤rtused? (Enamasti on see puhas kettaruumi raiskamine, aga kui lugemisel olid, siis...)
        #Ćµieti on see spektri omadus, s.t. peaks nagu selles osas ka listi tegema; kui asi laiemaks ajada, siis on see ehk liiga spetsiifiline
        #teisalt, Ć¤kki see lugemisel saadud info siiski osutub kuidagi oluliseks? Samuti ka versiooniga, mis on siiski faili Ć¼ldomadus.

    def xVect(self):
        return [self.start + self.step * k for k in range(len(self.spc))]
        

class Spectra:

    def __init__(self,filename = None):
        self.spectra = []
        self.version = DOS3 #self.DOS3? Praegu DOS (uuem) versioon vaikimisi (wadabout WIN versioon?)
        if filename is not None:
            self.readSpc(filename)
            
    def __getitem__(self, no):
        return self.spectra[no]

    def __len__(self):
        return len(self.spectra)



    def readSpc(self, filename):
        
        file = open(filename, "rb")
        # kontrollime signatuuri
        str = file.read(30) #koos termineeriva nulliga
        if str[:-1] == 'SPECTRA - S.Savikhin Software':
            version = DOS1
        elif str[:-1]== b"SPECTRA - S.Savikhin 67\x00tware":
            version = DOS3
        elif str[:-2] == b'SPECTRA : S.Savikhin Softwar':
            version = WIN96
            file.seek(-2,1) #vĆµtame 2 baidi vĆµrra tagasi
        else:
            raise ValueError('Incorrect file format',filename)
        
        #versioonist sĆµltuvalt uint16 vĆµi uint32:
        lentype,lenlen = ("H",2) if version < WIN96  else ("L",4)
        noOfSpc, = struct.unpack('=' + lentype,file.read(lenlen))
        
        #struct.unpacki juures tingimata '=', sest eriti nt 'L' vĆµib muidu tahta 8-baidine olla.
        
        #nĆ¼Ć¼d tuleks positsioonitabel lugeda
        #posTable = array.array('L')
        file.seek( -4 * noOfSpc, 2)
        posTable = list(struct.unpack('='+'L'*noOfSpc, file.read(4*noOfSpc)))
        #posTable.fromfile(file, noOfSpc)
       
        # ja hakkamegi spektreid jĆ¤rjest lugema
        for i in range(noOfSpc):
            file.seek(posTable[i])
            
            if (version == WIN96):
                file.seek(4, 1) #siin on mingid 4 baiti, mida ei oska tĆ¤pselt tĆµlgendada, tavaliselt 03 00 00 00
            start,step,len,date = struct.unpack("=dd" + lentype + "L", file.read(20 + lenlen))
            if (version == WIN96):
                #mitu baiti punkti kohta?
                dblPrec = (struct.unpack("=B",file.read(1))[0] == 8)
            else:
                dblPrec = False
            
            if version == DOS1:
                #versioon 1 puhul on kommendi pikkus teada (pĆ¤Ć¤ditud nullidega)
                comment = file.read(30)
                comment = comment[:comment.find('\x00')]
            
            #loeme nĆ¼Ć¼d spektrid ka sisse:
            pointTable = array.array("d" if dblPrec else "f")
            pointTable.fromfile(file, len)
            
            #lĆµpuks ka komment uuemate versioonide jaoks
            #WIN96 puhul peaks meil olema pikkus teada
            #aga DOS3 puhul - lihtsalt lugeda nullini?
            if version == WIN96:
                comlen, = struct.unpack("=L",file.read(4))
                comment = file.read(comlen - 1) #termineeriva nulli vĆµtame maha
            elif version == DOS3:
                comment = ''
                while True:
                    c = file.read(1)
                    if c == b'\x00':
                        break
                    comment += c.decode("latin1")
                    
							
            
            # ja kui edukalt siiani jĆµutud, vĆµib korraga kĆµik vĆ¤Ć¤rtused objektile omistada
            self.addSpc(pointTable.tolist(), start, step, comment, date)
            self.spectra[-1].dblPrec |= dblPrec
            if self.version < version:
                self.version = version
        file.close()

    def writeSpc(self, filename):
        
        file = open(filename, "wb")
        
        if self.version == DOS1:
            file.write("SPECTRA - S.Savikhin Software\x00")
        elif self.version == DOS3:
            file.write(str("SPECTRA - S.Savikhin 67\x00tware\x00").encode("utf-8"))
        else:
            file.write(b"SPECTRA : S.Savikhin Softwar")
        
        #versioonist sĆµltuvalt uint16 vĆµi uint32:
        lentype ="H" if self.version < WIN96 else "L"
        file.write(struct.pack('=' + lentype,len(self.spectra)))
        #struct.packi juures siin ja igal pool = oluline, muidu vahel vĆµib pikkus erineda!
       
        #pos. tabel lihtsalt listina:
        posTable = [] 
        
        #aga prooviks hoida sellist joont,et phm. saaks ka suvalise listi spektrinumbreid ette anda faili kirjutamiseks
        #siis pole muud, kui et siin tuleb range asemel mingi list ja posTable tuleb vastavalt tĆ¤ita
        
        for s in self.spectra:
            posTable.append(file.tell())
            #WIN96 korral tuleb kĆµigepealt tundmatu sekvents, milleks kĆµlbab 3,0,0,0
            if (self.version == WIN96):
                file.write(struct.pack("=L",3))
            #kirjutame headeri
            file.write(struct.pack("=dd" + lentype + "L",s.start, s.step, len(s.spc), s.date))
            #"=" on siin vajalik, et vĆ¤ltida paddingut len jaoks
            #versioon 1 puhul ka kommendi
            if self.version == DOS1:
                #siin peab vaatama, et komment Ć¼le 29 mĆ¤rgi pole (pikkuseks 30 pannes tekib termineeriv null iseenesest)
                file.write(struct.pack("30s",s.comment[:29]))
            elif self.version == WIN96:
                #siis peab kirjutama, mitu baiti punkti kohta
                file.write(struct.pack("=B", 8 if s.dblPrec else 4))
            
            #NĆ¼Ć¼d siis punktid, siin kasutame array-d
            pointTable = array.array("d" if s.dblPrec else "f")
            pointTable.fromlist(s.spc)
            pointTable.tofile(file)
            #ja siis jĆ¤Ć¤b veel komment vanema kui esimese versiooni korral
            if self.version > DOS1:
                if self.version == WIN96:
                    file.write(struct.pack("=L",len(s.comment) + 1)) #kui WIN versioon, siis on siin pikkus koos
                    #termineeriva nulliga
                file.write(bytes(s.comment, "utf8"))
                #kas nii saab? siis vĆµiks commarr-i Ć¤ra koristada
                file.write(struct.pack("=b",0)) #termineeriv 0
        #pos.tabel ka
        
        file.write(struct.pack('=' + 'L'*len(posTable), *posTable))
            
        #siis peaks kĆµik olema
        file.close()
    
    def addSpc(self, spc = [], start = 0.0, step = 1.0, comment = "", date = None, pos = None):
        #Spektri lisamise abiprogramm, annab vĆµimalikult palju vaikimisi ette ja vĆµimaldab ka vahelelisamist jne
        #pos None vĆµi olemasolevast hulgast suurem = lĆ¤heb lĆµppu
        #date None on jooksev (ega ma ei teagi, mis formaadis teda siin veel lubada? Hetkel paneks vist igal juhul jooksva)
        
        if ((pos is None) or (pos < 0) or (pos >= len(self.spc))): #HM... kas pos on 0- vĆµi 1-based?
            pos = len(self.spectra) # siis lĆ¤heb listi lĆµppu
        
        newSpc = Spc(spc, start, step, comment, date)
        self.spectra.insert(pos,newSpc)
        
        return pos

    
    def swapSpc(self, spno1, spno2):
        
        if (spno1 < 0 ) or (spno1 >= len(self.spc)) or (spno2 < 0 ) or (spno2 >= len(self.spc)) or (spno1 == spno2):
            return
        self.spectra[spno1],self.spectra[spno2] = self.spectra[spno2], self.spectra[spno1]
        return
