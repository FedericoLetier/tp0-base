package common

import (
	"context"
	"bufio"
	"fmt"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	keep_running bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
		keep_running: true,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

func (c *Client) sendMessage() {
	fmt.Fprintf(
		c.conn,
		"[CLIENT %v] Message N°%v\n",
		c.config.ID,
		msgID,
	)
}

func (c *Client) receiveMessage () {
	bufio.NewReader(c.conn).ReadString('\n')
}

func (c *Cliet) waitAfterSending {
	select {
	case <-ctx.Done():
    	return
	case <-time.After(c.config.LoopPeriod):
	}
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(ctx context.Context) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed	
	for msgID := 1; msgID <= c.config.LoopAmount && c.keep_running; msgID++ {
		// Create the connection the server in every loop iteration. Send an		
		c.createClientSocket()
			
		// TODO: Modify the send to avoid short-write
		c.sendMessage()
		msg, err := c.receiveMessage()
		c.conn.Close()

		if err != nil && c.keep_running {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			continue
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
		c.config.ID, 
		msg,
		)

		if !c.keep_running {
			continue
		}
		
		// Wait a time between sending one message and the next one
		c.waitAfterSending()
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) Close() {
	log.Infof("action: shutdown | result: success | info: Client shutdown completed")
	c.conn.Close()
	c.keep_running = false
}
