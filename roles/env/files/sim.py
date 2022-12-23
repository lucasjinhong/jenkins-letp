
class SIMInfo:
    def __init__(
            self, issuer, iins, apns, m1_bands, nb1_bands, default_apn=None):
        self.issuer = issuer
        self.iins = iins
        self.apns = apns
        self.m1_bands = m1_bands
        self.nb1_bands = nb1_bands
        if default_apn:
            self.default_apn = default_apn
        else:
            self.default_apn = self.apns[0].name

    def get_apn(self, name):
        return next((apn for apn in self.apns if apn.name == name), None)


class APN:
    def __init__(self, name, apn, pdp_type="IP"):
        self.name = name
        self.pdp_type = pdp_type
        self.apn = apn


class IIN:
    # Pass in ii_min (and optionall ii_max) to specify an integer range
    # to match against.
    # Pass a list to iis to specify a list of valid ii codes
    # (used for codes that start with a 0)
    def __init__(
            self,
            cc,
            ii_min: int = None,
            mii: int = 89,
            ii_max: int = None,
            iis: list = None):
        if (ii_min and iis) or (not ii_min and not iis):
            raise ValueError(
                    "Only one of ii_min or iis can be not None")

        self.cc = cc

        if ii_min:
            self.ii_min = ii_min
            self.mii = mii
            if ii_max:
                self.ii_max = ii_max
            else:
                self.ii_max = ii_min
            if len(str(self.ii_max)) != len(str(self.ii_min)):
                raise ValueError(
                        "IIN ranges must contain the same number of digits")
            self._type = "range"
        elif iis:
            self.iis = iis
            self._type = "list"


    def match(self, iin: int):
        iin = str(iin)
        cmp_str = "{mii}{cc}".format(mii=self.mii, cc=self.cc)
        if iin.startswith(cmp_str):
            ii = iin[len(cmp_str):len(cmp_str) + len(str(self.ii_max))]
            if self._type == "range":
                ii = int(ii)
                if self.ii_min <= ii <= self.ii_max:
                    return True
            elif self._type == "list":
                if ii in self.iis:
                    return True
        return False

    def to_string(self):
        if self._type == "range":
            if self.ii_min != self.ii_max:
                out = "{mii}{cc}({ii_min}-{ii_max})".format(
                        mii=self.mii,
                        cc=self.cc,
                        ii_min=self.ii_min,
                        ii_max=self.ii_max)
            else:
                out = "{mii}{cc}{ii}".format(
                        mii=self.mii,
                        cc=self.cc,
                        ii=self.ii_min)
        elif self._type == "list":
            out = "{mii}{cc}{ii}".format(
                    mii=self.mii,
                    cc=self.cc,
                    ii=self.iis)
        return out

    def __repr__(self):
        return "<IIN {iin}>".format(
                iin=self.to_string())


class LTEBand:
    def __init__(self, bands):
        self.bands = bands

    @classmethod
    def from_bitmap(cls, bitmap):
        bitmap = int(bitmap, 16)

        band = 1
        bands = []
        while bitmap:
            if bitmap & 1:
                bands.append(band)

            bitmap = bitmap >> 1
            band += 1

        return cls(bands)

    def to_bitmap(self):
        bitmap = 0
        for b in self.bands:
            bitmap |= 1 << (int(b)-1)
        return hex(bitmap)[2:]


# Information pulled from requrement 7 of
# https://confluence.sierrawireless.com/display/CBUP/R2C+-+Generic+Module+Requirements
_sims = [
        SIMInfo(
            "sierra_esim",
            [
                # Technically this is a MBQT IIN
                IIN(33, ii_min=250, ii_max=254),
            ],
            [
                APN("lp", "lp.fota.swir"),
            ],
            LTEBand([12]),
            LTEBand([]),
            "lp"
            ),
        SIMInfo(
            "sierra",
            [
                # Owned by OBERTHUR TECHNOLOGIES?
                IIN(33, 24),
            ],
            [
                APN("lp", "lpwa.swir"),
                APN("lp", "fota.swir")
            ],
            LTEBand([12]),
            LTEBand([12]),
            "lp"
            ),
        SIMInfo(
            "sierra_new_plastic",
            [
                # Technically this is a MBQT IIN
                IIN(33, ii_min=255, ii_max=259),
            ],
            [
                APN("lp", "lp.swir"),
            ],
            LTEBand([12]),
            LTEBand([12]),
            "lp"
            ),
        SIMInfo(
            "telus",
            [
                IIN(12, 2300),
                IIN(30, 2220)
            ],
            [
                APN("default", "sp.telus.com", "IPV4V6")
            ],
            LTEBand([12]),
            LTEBand([]),
            "default"
            ),
        SIMInfo(
            "amarisoft",
            [
                IIN("01", 41),
                IIN("86", 41)
            ],
            [
                APN("default", "default", "IP"),
                APN("default2", "internet", "IP"),
                APN("ims", "ims", "IPV4V6"),
                # Modify for Taipei amarisoft
                APN("pap", "pap", "IP"),
                APN("chap", "chap", "IP")
                # APN("pap", "defaultauthpap", "IP"),
                # APN("chap", "defaultauthchap", "IP")
            ],
            LTEBand([5]),   # Change M1 to band 5 for TPE Amarisoft
            LTEBand([20]),  # Change NB-IOT to band 20 for TPE Amarisoft
            "default"
            ),
        SIMInfo(
            "rogers",
            [
                IIN(30, 2720)
            ],
            [
                APN("", "swi3.ca.apn", "IPV4V6")
            ],
            LTEBand([12]),
            LTEBand([12]),
            "default"
            ),
        SIMInfo(
            "at&t",
            [
                IIN("01", 1703)
            ],
            [
                APN("", "mnrx11.com.attz", "IP"),
                APN("", "attm2mglobal", "IPV4V6")
            ],
            LTEBand([12]),
            LTEBand([20]),
            "default"
            ),
        SIMInfo(
            "verizon",
            [
                IIN(14, 8000)
            ],
            [
                APN("", "num.vzwentp", "IP")
            ],
            LTEBand([25]),
            LTEBand([20]),
            "default"
            ),
        SIMInfo(
            "tmo",
            [
                IIN("01", 2608)
            ],
            [
                APN("", "tm1nmrx", "IP")
            ],
            LTEBand([25]),
            LTEBand([20]),
            "default"
            ),
        SIMInfo(
            "ChungHwa",
            [
                IIN("886", 92)
            ],
            [
                APN("default", "internet", "IP")
            ],
            LTEBand([3]),
            LTEBand([8]),
            "default"
            )
        ]


def iccid_to_siminfo(iccid):
    return next(
            (si for si in _sims
                if any([i.match(iccid) for i in si.iins])),
            None)


