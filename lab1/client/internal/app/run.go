package app

import (
	"client/internal/config"
	"log/slog"
	"net"
)

func Run(cfg *config.Config) {
	udpAddr := &net.UDPAddr{
		IP:   cfg.GetIpv4Addr(),
		Port: cfg.Port,
	}

	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		slog.Error("listening udp", "config", cfg)
	}
	defer conn.Close()

}
