package common

import (
	"context"
	"time"

	"github.com/op/go-logging"
)

type Bet struct {
    Name    string
    Surname  string
    Document string
    Birth string
    Number    string
}

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
	bet Bet
	socket *ClientSocket
	keep_running bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig, bet Bet) *Client {
	client := &Client{	
		config: config,
		bet: bet,
		keep_running: true,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	socket, err := NewClientSocket(c.config.ServerAddress)
	
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.socket = socket
	return nil
}

func (c *Client) sendBet() error {
	err := c.socket.SendBet(c.bet)
	if err != nil {
		log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
	}
	return err
}

func (c *Client) receiveMessage() {
	msg, err := c.socket.ReceiveResponse()

	if msg != "SUCCESS: Bet stored\n" {
		if c.keep_running {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
		}
		return
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %s | number: %s", 
		c.bet.Document, c.bet.Number)
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(ctx context.Context) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed	
	for msgID := 1; msgID <= c.config.LoopAmount && c.keep_running; msgID++ {
		// Create the connection the server in every loop iteration. Send an		
		if c.createClientSocket() == nil {
			err := c.sendBet()
			if err != nil {
				continue
			}
			c.receiveMessage()
		}

		if !c.keep_running {
			continue
		}
	
		// Wait a time between sending one message and the next on: receione
		select {
		case <-ctx.Done():
    		return
		case <-time.After(c.config.LoopPeriod):
		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) Close() {
	log.Infof("action: shutdown | result: success | info: Client shutdown completed")
	c.socket.Close()
	c.keep_running = false
}
