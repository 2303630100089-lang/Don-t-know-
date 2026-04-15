# 74. Algorithm: WebRTC Conferencing

## Overview

Real-time WebRTC conferencing algorithm covering call initiation, server-based signaling, peer-to-peer connection establishment, fast media streaming, and secure encryption.

## Algorithm Steps

### Step 1: User Initiates Call
- User requests to start a call (1:1 or group).
- Call request sent to signaling server with participants list.
- Call type determined: audio-only, video, screen share.
- Participant availability checked (online status, DND settings).
- Ring notification sent to all participants.

### Step 2: Signaling via Server
- **Signaling Server**: WebSocket-based for real-time message exchange.
- **SDP Exchange**: Session Description Protocol offers and answers.
  - Offer: caller's media capabilities (codecs, resolution, bandwidth).
  - Answer: callee's accepted capabilities.
- **ICE Candidates**: Interactive Connectivity Establishment for NAT traversal.
  - STUN server: discover public IP/port.
  - TURN server: relay media when direct connection impossible.
- **Session Control**: Join, leave, mute, camera toggle signals.

### Step 3: Peer-to-Peer Connection
- **1:1 Calls**: Direct P2P connection via DTLS/SRTP.
- **Group Calls (SFU)**: Selective Forwarding Unit relays media.
  - Each participant sends one stream to SFU.
  - SFU selectively forwards to other participants.
  - Bandwidth-efficient: no full mesh needed.
- **Simulcast**: Sender transmits multiple quality layers; SFU selects optimal.
- **ICE Gathering**: Collect all possible connection paths (host, srflx, relay).

### Step 4: Fast Media Streaming
- **Codecs**: VP8/VP9/H.264 for video, Opus for audio.
- **Adaptive Bitrate**: Quality adjusts based on available bandwidth.
- **Bandwidth Estimation**: REMB/TWCC for sender-side bitrate control.
- **Jitter Buffer**: Smooth out network jitter for consistent playback.
- **FEC (Forward Error Correction)**: Recover lost packets without retransmission.
- **Latency Target**: < 200ms end-to-end for real-time feel.

### Step 5: Secure Encryption
- **DTLS**: Datagram TLS for key exchange.
- **SRTP**: Secure Real-time Transport Protocol for media encryption.
- **E2E Encryption**: Optional end-to-end encryption (Insertable Streams API).
- **Authentication**: Participants verified via signaling server.
- **Key Rotation**: Encryption keys rotated periodically during call.

## Pseudocode

```
// Caller side
function initiateCall(caller_id, participants, call_type):
    call_id = generateCallId()
    
    // Step 1: Create call session
    session = {
        id: call_id,
        initiator: caller_id,
        participants: participants,
        type: call_type,
        created_at: now()
    }
    
    signalingServer.createSession(session)
    
    // Notify participants
    for participant in participants:
        if participant != caller_id:
            signalingServer.send(participant, {
                type: "call_invite",
                call_id, caller_id, call_type
            })
    
    // Step 2: Create offer
    peerConnection = new RTCPeerConnection(config={
        iceServers: [
            { urls: "stun:stun.example.com:3478" },
            { urls: "turn:turn.example.com:3478", credentials: ... }
        ]
    })
    
    // Add local media
    localStream = await getUserMedia({
        video: call_type != "audio",
        audio: true
    })
    localStream.tracks.forEach(t => peerConnection.addTrack(t))
    
    // Enable simulcast for group calls
    if participants.length > 2:
        enableSimulcast(peerConnection)
    
    // Create and send offer
    offer = await peerConnection.createOffer()
    await peerConnection.setLocalDescription(offer)
    
    signalingServer.send("offer", {
        call_id, sdp: offer.sdp, from: caller_id
    })
    
    // Step 2: Exchange ICE candidates
    peerConnection.onicecandidate = (event) =>
        signalingServer.send("ice_candidate", {
            call_id, candidate: event.candidate, from: caller_id
        })

// Callee side
function onCallInvite(invite):
    // Step 2: Receive offer and create answer
    peerConnection = new RTCPeerConnection(config)
    
    await peerConnection.setRemoteDescription(invite.offer.sdp)
    
    localStream = await getUserMedia({video: true, audio: true})
    localStream.tracks.forEach(t => peerConnection.addTrack(t))
    
    answer = await peerConnection.createAnswer()
    await peerConnection.setLocalDescription(answer)
    
    signalingServer.send("answer", {
        call_id: invite.call_id, sdp: answer.sdp
    })

// SFU for group calls
function sfuForward(call_id, sender_id, media_packet):
    session = getSession(call_id)
    
    for participant in session.participants:
        if participant.id == sender_id:
            continue
        
        // Select quality layer based on participant's bandwidth
        layer = selectSimulcastLayer(
            sender_layers=media_packet.layers,
            receiver_bandwidth=participant.estimated_bandwidth
        )
        
        forwardPacket(participant.connection, layer)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Call setup time | < 2 seconds |
| Audio latency (P2P) | < 150ms |
| Video latency (P2P) | < 200ms |
| SFU forwarding delay | < 50ms |
| Packet loss recovery (FEC) | Up to 20% loss |
