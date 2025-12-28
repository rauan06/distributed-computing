package config

import (
	"net"

	"github.com/caarlos0/env/v11"
)

type Config struct {
	Addr string `env:"ADDR"`
	Port int    `env:"PORT"`
}

func New() (*Config, error) {
	var cfg = &Config{}

	err := env.Parse(cfg)
	if err != nil {
		return nil, err
	}

	return cfg, nil
}

func (c *Config) GetIpv4Addr() net.IP {
	return net.ParseIP(c.Addr)
}
