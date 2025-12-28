package app

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"log/slog"
	"math/rand"
	"net"
	"os"
	"server/internal/config"
	"strconv"
	"sync"
	"time"
)

type Service struct {
	requestLog sync.Map
}

type RPCRequest struct {
	RequestID string                 `json:"request_id"`
	Method    string                 `json:"method"`
	Params    map[string]interface{} `json:"params"`
	Timestamp int64                  `json:"timestamp,omitempty"`
}

type RPCResponse struct {
	RequestID string      `json:"request_id"`
	Result    interface{} `json:"result,omitempty"`
	Error     string      `json:"error,omitempty"`
	Status    string      `json:"status"`
}

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

	for {
		buffer := make([]byte, 1024)

		n, addr, err := conn.ReadFromUDP(buffer)
		if err != nil {
			slog.Error("error reading from udp", "error", err)
			continue
		}

		go handleMessage(conn, addr, buffer[:n])
	}
}

func (s *Service) ParseInput(buffer []byte) (*RPCRequest, error) {
	var req RPCRequest
	if err := json.Unmarshal(buffer, &req); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %v", err)
	}

	if req.RequestID == "" {
		return nil, fmt.Errorf("request_id is required")
	}

	if req.Method == "" {
		return nil, fmt.Errorf("method is required")
	}

	return &req, nil
}

// HandleErr sends error response
func (s *Service) HandleErr(conn *net.UDPConn, addr *net.UDPAddr, message string, err error) {
	resp := RPCResponse{
		Status: "ERROR",
		Error:  fmt.Sprintf("%s: %v", message, err),
	}

	respData, _ := json.Marshal(resp)
	conn.WriteToUDP(respData, addr)

	log.Printf("Error: %s - %v", message, err)
}

func (s *Service) ExecuteMethod(req *RPCRequest) *RPCResponse {
	if _, loaded := s.requestLog.LoadOrStore(req.RequestID, true); loaded {
		return &RPCResponse{
			RequestID: req.RequestID,
			Status:    "DUPLICATE",
			Error:     "Request already processed",
		}
	}

	// Clean up old requests periodically (in production, use proper cleanup)
	go func() {
		time.Sleep(5 * time.Minute)
		s.requestLog.Delete(req.RequestID)
	}()

	var result interface{}
	var err error

	if rand.Intn(5) == 0 {
		log.Printf("Simulating delay for request %s", req.RequestID)
		time.Sleep(3 * time.Second)
	}

	switch req.Method {
	case "add":
		result, err = s.add(req.Params)
	case "subtract":
		result, err = s.subtract(req.Params)
	case "multiply":
		result, err = s.multiply(req.Params)
	case "divide":
		result, err = s.divide(req.Params)
	case "get_time":
		result, err = s.getTime(req.Params)
	case "reverse_string":
		result, err = s.reverseString(req.Params)
	case "echo":
		result, err = s.echo(req.Params)
	default:
		err = fmt.Errorf("unknown method: %s", req.Method)
	}

	if err != nil {
		return &RPCResponse{
			RequestID: req.RequestID,
			Status:    "ERROR",
			Error:     err.Error(),
		}
	}

	return &RPCResponse{
		RequestID: req.RequestID,
		Result:    result,
		Status:    "OK",
	}
}

// RPC Methods Implementation
func (s *Service) add(params map[string]interface{}) (interface{}, error) {
	a, ok1 := params["a"].(float64)
	b, ok2 := params["b"].(float64)

	if !ok1 || !ok2 {
		return nil, fmt.Errorf("parameters 'a' and 'b' must be numbers")
	}

	return a + b, nil
}

func (s *Service) subtract(params map[string]interface{}) (interface{}, error) {
	a, ok1 := params["a"].(float64)
	b, ok2 := params["b"].(float64)

	if !ok1 || !ok2 {
		return nil, fmt.Errorf("parameters 'a' and 'b' must be numbers")
	}

	return a - b, nil
}

func (s *Service) multiply(params map[string]interface{}) (interface{}, error) {
	a, ok1 := params["a"].(float64)
	b, ok2 := params["b"].(float64)

	if !ok1 || !ok2 {
		return nil, fmt.Errorf("parameters 'a' and 'b' must be numbers")
	}

	return a * b, nil
}

func (s *Service) divide(params map[string]interface{}) (interface{}, error) {
	a, ok1 := params["a"].(float64)
	b, ok2 := params["b"].(float64)

	if !ok1 || !ok2 {
		return nil, fmt.Errorf("parameters 'a' and 'b' must be numbers")
	}

	if b == 0 {
		return nil, fmt.Errorf("division by zero")
	}

	return a / b, nil
}

func (s *Service) getTime(params map[string]interface{}) (interface{}, error) {
	return time.Now().Unix(), nil
}

func (s *Service) reverseString(params map[string]interface{}) (interface{}, error) {
	str, ok := params["s"].(string)
	if !ok {
		return nil, fmt.Errorf("parameter 's' must be a string")
	}

	runes := []rune(str)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}

	return string(runes), nil
}

func (s *Service) echo(params map[string]interface{}) (interface{}, error) {
	return params, nil
}

func handleMessage(conn *net.UDPConn, addr *net.UDPAddr, buffer []byte) {
	service := &Service{}

	msg, err := service.ParseInput(buffer)
	if err != nil {
		service.HandleErr(conn, addr, "error parsing inputs", err)
		return
	}

	log.Printf("Received request: %s from %s", msg.Method, addr.String())

	// Process request
	resp := service.ExecuteMethod(msg)

	// Marshal response
	respData, err := json.Marshal(resp)
	if err != nil {
		service.HandleErr(conn, addr, "error marshaling response", err)
		return
	}

	// Send response
	_, err = conn.WriteToUDP(respData, addr)
	if err != nil {
		log.Printf("Error sending response: %v", err)
	}

	log.Printf("Sent response for request: %s", msg.RequestID)
}

func Run(cfg *Config) {
	udpAddr := &net.UDPAddr{
		IP:   cfg.GetIpv4Addr(),
		Port: cfg.Port,
	}

	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		log.Fatal("Error listening UDP:", err)
	}
	defer conn.Close()

	log.Printf("RPC Server listening on %s:%d", cfg.Host, cfg.Port)
	log.Printf("Available methods: add, subtract, multiply, divide, get_time, reverse_string, echo")

	for {
		buffer := make([]byte, 1024)

		n, addr, err := conn.ReadFromUDP(buffer)
		if err != nil {
			log.Printf("Error reading from UDP: %v", err)
			continue
		}

		go handleMessage(conn, addr, buffer[:n])
	}
}

// Client implementation
type RPCClient struct {
	ServerAddr *net.UDPAddr
	Conn       *net.UDPConn
	Timeout    time.Duration
	MaxRetries int
}

func NewRPCClient(serverHost string, serverPort int, timeout time.Duration, maxRetries int) (*RPCClient, error) {
	serverAddr, err := net.ResolveUDPAddr("udp", fmt.Sprintf("%s:%d", serverHost, serverPort))
	if err != nil {
		return nil, err
	}

	conn, err := net.ListenUDP("udp", nil)
	if err != nil {
		return nil, err
	}

	return &RPCClient{
		ServerAddr: serverAddr,
		Conn:       conn,
		Timeout:    timeout,
		MaxRetries: maxRetries,
	}, nil
}

func (c *RPCClient) Call(method string, params map[string]interface{}) (*RPCResponse, error) {
	requestID := generateRequestID()

	req := RPCRequest{
		RequestID: requestID,
		Method:    method,
		Params:    params,
		Timestamp: time.Now().Unix(),
	}

	reqData, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	var lastErr error
	for retry := 0; retry <= c.MaxRetries; retry++ {
		if retry > 0 {
			log.Printf("Retry %d for request %s", retry, requestID)
		}

		ctx, cancel := context.WithTimeout(context.Background(), c.Timeout)
		defer cancel()

		// Send request
		_, err = c.Conn.WriteToUDP(reqData, c.ServerAddr)
		if err != nil {
			lastErr = err
			continue
		}

		// Wait for response with timeout
		responseChan := make(chan *RPCResponse)
		errorChan := make(chan error)

		go func() {
			buffer := make([]byte, 1024)
			n, _, err := c.Conn.ReadFromUDP(buffer)
			if err != nil {
				errorChan <- err
				return
			}

			var resp RPCResponse
			if err := json.Unmarshal(buffer[:n], &resp); err != nil {
				errorChan <- err
				return
			}

			responseChan <- &resp
		}()

		select {
		case resp := <-responseChan:
			return resp, nil
		case err := <-errorChan:
			lastErr = err
		case <-ctx.Done():
			lastErr = fmt.Errorf("timeout after %v", c.Timeout)
		}

		// Wait before retry
		if retry < c.MaxRetries {
			time.Sleep(time.Duration(retry+1) * 500 * time.Millisecond)
		}
	}

	return nil, fmt.Errorf("max retries exceeded: %v", lastErr)
}

func generateRequestID() string {
	return fmt.Sprintf("%d-%d", time.Now().UnixNano(), rand.Intn(1000))
}

// Example client usage
func runClientExample() {
	client, err := NewRPCClient("127.0.0.1", 5000, 2*time.Second, 3)
	if err != nil {
		log.Fatal(err)
	}
	defer client.Conn.Close()

	// Test different RPC calls
	tests := []struct {
		method string
		params map[string]interface{}
	}{
		{"add", map[string]interface{}{"a": 5, "b": 7}},
		{"subtract", map[string]interface{}{"a": 10, "b": 3}},
		{"multiply", map[string]interface{}{"a": 4, "b": 6}},
		{"divide", map[string]interface{}{"a": 15, "b": 3}},
		{"get_time", map[string]interface{}{}},
		{"reverse_string", map[string]interface{}{"s": "hello"}},
		{"echo", map[string]interface{}{"test": "data", "number": 42}},
	}

	for _, test := range tests {
		fmt.Printf("\nCalling %s with params %v\n", test.method, test.params)

		resp, err := client.Call(test.method, test.params)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			continue
		}

		fmt.Printf("Response: Status=%s, Result=%v, Error=%s\n",
			resp.Status, resp.Result, resp.Error)
	}
}

func main() {
	// Default configuration
	cfg := &Config{
		Host: "0.0.0.0",
		Port: 5000,
	}

	// Parse command line arguments
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "server":
			if len(os.Args) > 2 {
				port, err := strconv.Atoi(os.Args[2])
				if err == nil {
					cfg.Port = port
				}
			}
			Run(cfg)
		case "client":
			runClientExample()
		default:
			fmt.Println("Usage:")
			fmt.Println("  go run main.go server [port] - Start RPC server")
			fmt.Println("  go run main.go client      - Run client example")
			fmt.Println("Default port: 5000")
		}
	} else {
		fmt.Println("Please specify 'server' or 'client' mode")
		fmt.Println("Example: go run main.go server 5000")
	}
}
