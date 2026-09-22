#!/usr/bin/env python3
from pathlib import Path

router = Path("wgslirpy/crates/libwgslirpy/src/router.rs")
serve_tcp = Path("wgslirpy/crates/libwgslirpy/src/router/serve_tcp.rs")

r = router.read_text()
s = serve_tcp.read_text()

old = """    /// Listen these TCP ports on host and direct connections into the internal network.\n    pub incoming_tcp: Vec<PortForward>,\n}"""
new = """    /// Listen these TCP ports on host and direct connections into the internal network.\n    pub incoming_tcp: Vec<PortForward>,\n\n    /// Rewrite destination TCP endpoints for connections coming from WireGuard.\n    /// The original endpoint remains visible to the WireGuard client; only the\n    /// host-side TCP connection uses the mapped destination.\n    pub outgoing_tcp: Vec<OutgoingPortForward>,\n}"""
assert old in r
r = r.replace(old, new, 1)

old = """pub struct PortForward {\n    /// Which socket address to use to bind the host socket to.\n    pub host: SocketAddr,\n\n    /// Typically incoming connection or datagram address is also used as a source address within internal network.\n    /// Setting `src` allows you to override this and just use source fixed address.\n    /// \n    /// If port part is `0` and this port forward is used for `incoming_tcp`, the port number is filled in with nonzero value is some way.\n    pub src: Option<SocketAddr>,\n\n    /// Where within our internal network to forward connections or datagrams to.\n    pub dst: SocketAddr,\n}\n"""
new = old + """\n/// Destination rewrite for TCP connections originating inside the WireGuard tunnel.\n#[derive(Debug, Clone, Copy)]\npub struct OutgoingPortForward {\n    /// Endpoint as seen by the WireGuard client.\n    pub src: SocketAddr,\n\n    /// Actual host-side endpoint to connect to.\n    pub dst: SocketAddr,\n}\n\nfn map_outgoing_tcp(endpoint: IpEndpoint, mappings: &[OutgoingPortForward]) -> IpEndpoint {\n    mappings\n        .iter()\n        .find(|m| IpEndpoint::from(m.src) == endpoint)\n        .map(|m| IpEndpoint::from(m.dst))\n        .unwrap_or(endpoint)\n}\n"""
assert old in r
r = r.replace(old, new, 1)

old = """    let mtu = opts.mtu;\n    let tcp_buffer_size = opts.tcp_buffer_size;\n    let mut table"""
new = """    let mtu = opts.mtu;\n    let tcp_buffer_size = opts.tcp_buffer_size;\n    let outgoing_tcp = opts.outgoing_tcp;\n    let mut table"""
assert old in r
r = r.replace(old, new, 1)

old = """                let tx_to_wg2 = tx_to_wg.clone();\n                let (tx_persocket_fromwg, rx_persocket_fromwg) = channel(4);\n                let k = entry.key().clone();\n                let tx_closes = tx_closes.clone();\n                tokio::spawn(async move {\n                    let ret = match k {\n                        NatKey::Tcp {\n                            external_side,\n                            client_side: _,\n                        } => {\n                            serve_tcp::serve_tcp(\n                                tx_to_wg2,\n                                rx_persocket_fromwg,\n                                external_side,\n                                serve_tcp::ServeTcpMode::Outgoing,\n                                mtu,\n                                tcp_buffer_size,\n                            )\n                            .await\n                        }"""
new = """                let tx_to_wg2 = tx_to_wg.clone();\n                let (tx_persocket_fromwg, rx_persocket_fromwg) = channel(4);\n                let k = entry.key().clone();\n                let tx_closes = tx_closes.clone();\n                let outgoing_tcp2 = outgoing_tcp.clone();\n                tokio::spawn(async move {\n                    let ret = match k {\n                        NatKey::Tcp {\n                            external_side,\n                            client_side: _,\n                        } => {\n                            let target_addr = map_outgoing_tcp(external_side, &outgoing_tcp2);\n                            if target_addr != external_side {\n                                info!(\"TCP destination rewrite: {} -> {}\", external_side, target_addr);\n                            }\n                            serve_tcp::serve_tcp(\n                                tx_to_wg2,\n                                rx_persocket_fromwg,\n                                external_side,\n                                serve_tcp::ServeTcpMode::Outgoing { target_addr },\n                                mtu,\n                                tcp_buffer_size,\n                            )\n                            .await\n                        }"""
assert old in r
r = r.replace(old, new, 1)
router.write_text(r)

# Test BoringTun 0.7.0. BoringTun 0.7.1 is intentionally not selected here because upstream issue #495 reports a session regression in the Tunn library API matching this application architecture.
cargo = Path("wgslirpy/crates/libwgslirpy/Cargo.toml")
cc = cargo.read_text()
old = 'boringtun = "0.6.0"'
assert old in cc
cargo.write_text(cc.replace(old, 'boringtun = "0.7.0"', 1))

old = """pub enum ServeTcpMode {\n    Outgoing,\n    Incoming {"""
new = """pub enum ServeTcpMode {\n    Outgoing {\n        /// Actual host-side endpoint to connect to.\n        /// The externally visible endpoint remains the `external_addr` argument.\n        target_addr: IpEndpoint,\n    },\n    Incoming {"""
assert old in s
s = s.replace(old, new, 1)

old = """    let target_addr = match external_addr.addr {\n        IpAddress::Ipv4(x) => SocketAddr::new(std::net::IpAddr::V4(x.into()), external_addr.port),\n        IpAddress::Ipv6(x) => SocketAddr::new(std::net::IpAddr::V6(x.into()), external_addr.port),\n    };"""
new = """    let target_addr = match &mode {\n        ServeTcpMode::Outgoing { target_addr } => match target_addr.addr {\n            IpAddress::Ipv4(x) => SocketAddr::new(std::net::IpAddr::V4(x.into()), target_addr.port),\n            IpAddress::Ipv6(x) => SocketAddr::new(std::net::IpAddr::V6(x.into()), target_addr.port),\n        },\n        ServeTcpMode::Incoming { .. } => match external_addr.addr {\n            IpAddress::Ipv4(x) => SocketAddr::new(std::net::IpAddr::V4(x.into()), external_addr.port),\n            IpAddress::Ipv6(x) => SocketAddr::new(std::net::IpAddr::V6(x.into()), external_addr.port),\n        },\n    };"""
assert old in s
s = s.replace(old, new, 1)

old = """    let outgoing = matches!(mode, ServeTcpMode::Outgoing);"""
new = """    let outgoing = matches!(mode, ServeTcpMode::Outgoing { .. });"""
assert old in s
s = s.replace(old, new, 1)

old = """        ServeTcpMode::Outgoing => {"""
new = """        ServeTcpMode::Outgoing { .. } => {"""
assert old in s
s = s.replace(old, new, 1)

serve_tcp.write_text(s)

# Refresh the remembered WireGuard peer endpoint whenever a valid packet is
# received. With peer_endpoint = null, the client's UDP source port may change
# after a disconnect/reconnect; keeping the old endpoint causes handshake
# responses to be sent to the stale port.
wg = Path("wgslirpy/crates/libwgslirpy/src/wg.rs")
w = wg.read_text()

# Recreate only BoringTun's Tunn state after ConnectionExpired. Keep the
# Tokio UDP socket, router and Android service alive; only the expired
# WireGuard handshake/session state is replaced.
old = """use boringtun::noise::TunnResult;"""
new = """use boringtun::noise::{errors::WireGuardError, TunnResult};"""
assert old in w
w = w.replace(old, new, 1)

old = """                        TunnResult::Err(e) => {
                            error!("boringturn error: {:?}", e);
                        }"""
new = """                        TunnResult::Err(WireGuardError::ConnectionExpired) => {
                            error!("boringturn error: ConnectionExpired; recreating Tunn");
                            wg = boringtun::noise::Tunn::new(
                                self.private_key.clone(),
                                self.peer_key,
                                None,
                                self.keepalive_interval,
                                0,
                                None,
                            );
                        }
                        TunnResult::Err(e) => {
                            error!("boringturn error: {:?}", e);
                        }"""
assert old in w
w = w.replace(old, new, 1)
old = """                    if !matches!(tr_inner, TunnResult::Err(..)) {
                        if last_seen_recv_address.is_some()
                            && current_peer_addr.is_none()
                            && static_peer_addr.is_none()
                        {
                            current_peer_addr = last_seen_recv_address;
                        }
                    }"""
new = """                    if !matches!(tr_inner, TunnResult::Err(..)) {
                        if last_seen_recv_address.is_some() && static_peer_addr.is_none() {
                            current_peer_addr = last_seen_recv_address;
                        }
                    }"""
assert old in w
w = w.replace(old, new, 1)
wg.write_text(w)

print("Patched wgslirpy for outgoing TCP destination rewrites and peer endpoint refresh")
