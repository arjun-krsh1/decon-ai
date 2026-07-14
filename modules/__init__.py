from modules.geo import MODULE as GEO
from modules.design import MODULE as DESIGN
from modules.hr import MODULE as HR
from modules.product_intel import MODULE as PRODUCT_INTEL
from modules.market_share import MODULE as MARKET_SHARE
from modules.brand_media import MODULE as BRAND_MEDIA
from modules.comps_nemesis import MODULE as COMPS_NEMESIS

# DESIGN and BRAND_MEDIA are intentionally hidden from the UI. They stay imported and
# parked here so re-enabling either is a one-line change (move it into MODULES).
_HIDDEN = [DESIGN, BRAND_MEDIA]
MODULES = [GEO, HR, PRODUCT_INTEL, MARKET_SHARE, COMPS_NEMESIS]
BY_KEY = {m.key: m for m in MODULES}
