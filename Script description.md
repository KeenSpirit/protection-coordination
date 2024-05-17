# Protection Coordination
# https://mermaid-js.github.io.
# https://mermaid.live

oc_pickup()
The order of priority of constraints, from highest to lowest, is as follows:
1) Stay above load (load_factor) t
2) Stay below primary reach factor (oc_reach)
3) Stay below backup reach factor (oc_bu_reach)
4) Stay above conductor rating (rating_factor)
5) Stay below upstream relay pickup (upstream_oc)
6) Stay above downstream relay pickup (oc_pu_factor)
7) Stay above 4x downstream fuse rating (fuse_factor_02)
8) Stay above 3x downstream fuse rating (fuse_factor_01)

ef_pickup()
The order of priority of constraints, from highest to lowest, is as follows:
1) Stay above 10% of max load (load_factor)
2) Stay below primary reach factor (ef_reach)
3) Stay below backup reach factor (ef_bu_reach)
4) Stay below upstream relay pickup (upstream_ef)
5) Stay above downstream relay pickup (ef_pu_factor)
6) Stay below 33% of lowest fault (fault factor)

```mermaid
flowchart TD
A[ProtectionRelay]-- relays --> B[Generate relay settings]
B[Generate relay settings]-- relays --> C[Calculate relay trip times]
C[Calculate relay trip times]-- relays --> D[Calculate relay grade times]
D[Calculate relay grade times]-- relays --> E{Grading time acceptable?}
E-->|No| B
E-->|Yes|F[Calculate total relay trip time]
F-->G[Update best total trip time]
G-- while iterations < n --> B
G-- iterations = n --> H[best total trip time, best settings]
```

```mermaid
 classDiagram
      ProtectionRelay <|-- RelaySettings
      ProtectionRelay <|-- NetworkData
      ProtectionRelay <|-- RelayCT
      ProtectionRelay : name
      ProtectionRelay : technology
      ProtectionRelay : timing_error
      ProtectionRelay: cb_interrupt
      ProtectionRelay: overshoot
      ProtectionRelay: safety_margin
      ProtectionRelay: relset = RelaySettings(settings)
      ProtectionRelay: netdat = NetworkData(network)
      ProtectionRelay: ct = RelayCT(ct_data)
      class RelaySettings{
        status
        oc_pu
        oc_tms
        oc_curve
        oc_hiset
        oc_min_time
        oc_hiset2
        oc_min_time2
        ef_pu
        ef_tms
        ef_curve
        ef_hiset
        ef_min_time
        oc_hiset2
        oc_min_time2
      }
      class NetworkData{
        rating
        load
        ds_capacity
        max_3p_fl
        max_pg_fl
        min_2p_fl
        min_pg_fl
        max_tr_size
        tr_max_3p
        tr_max_pg
        downstream_devices
        upstream_devices
        get_clp()
        get_inrush()
        get_fuse_rating()
      }
      class RelayCT{
        saturation
        ect
      }
```
