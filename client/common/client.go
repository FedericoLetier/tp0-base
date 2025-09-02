package common

import (
	"time"
	"os"
	"bufio"
	"strings"
	"fmt"

	"github.com/op/go-logging"
)

const _SUCCESS_RESPONSE = "SUCCESS"
const CSV_SPLITTER = ","
const MAX_SIZE_BATCH = 8000

type Bet struct {
	AgencyID string
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
	MaxAmount	  int
}

type BetStored struct {
	sended bool
	bet Bet
	size int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	socket *ClientSocket
	keep_running bool
	previousBet BetStored
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	previousBet := BetStored{ sended: true, }
	client := &Client{	
		config: config,
		keep_running: true,
		previousBet: previousBet,
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

func (c *Client) receiveMessage(count int) error {
	msg, err := c.socket.ReceiveResponse()
	if err != nil {
    	log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
    	    c.config.ID,
    	    err,
    	)
    	return err
	}

	if !strings.Contains(msg, _SUCCESS_RESPONSE) {
	    err := fmt.Errorf("mensaje inesperado del server: %q", msg)
	    log.Errorf("action: receive_message | result: fail | client_id: %v | error: unexpected msg: %v",
	        c.config.ID,
	        err,
	    )
	    return err
	}

	log.Infof("action: apuesta_enviada | result: success | cantidad: %v", count)
	return nil
}

func (c *Client) parseLineAndReturnBet(scanner *bufio.Scanner) (Bet, bool, int) {
	line := scanner.Text()
	lineSize := len(line)
    fields := strings.Split(line, CSV_SPLITTER)
    if len(fields) < 5 {
        log.Errorf("action: parse_csv | result: fail | error: invalid line: %v", line)
        return Bet{}, false, 0
    }
    bet := Bet{
        AgencyID: c.config.ID,
        Name:     fields[0],
        Surname:  fields[1],
        Document: fields[2],
        Birth:    fields[3],
        Number:   fields[4],
    }
	return bet, true, lineSize
}

func (c *Client) savePreviousBet(bet Bet, size_line int, bytesReaded int) bool {
	if bytesReaded > MAX_SIZE_BATCH {
		log.Debugf("Lines exceed 8kb, sending less bets this round")
		c.previousBet.bet = bet
		c.previousBet.size = size_line
		c.previousBet.sended = false
		return true
	}
	return false
}

func (c *Client) addPreviousBet() ([]Bet, int, int) {
	bets := []Bet{}
	count := 0
	bytesReaded := 0
	if !c.previousBet.sended {
		bets = append(bets, c.previousBet.bet)
		c.previousBet.sended = true
		bytesReaded += c.previousBet.size
		count++	
	}
	return bets, count, bytesReaded
}

func (c *Client) sendBatch(scanner *bufio.Scanner) (bool, int, error) {
	bets, count, bytesReaded := c.addPreviousBet()
	keepReading := false
	for count < c.config.MaxAmount {
		keepReading = scanner.Scan()
		if !keepReading {
			break
		}
        bet, valid, lineSize := c.parseLineAndReturnBet(scanner)
		if !valid {
			continue
		}
		bytesReaded += lineSize
		saved := c.savePreviousBet(bet, lineSize, bytesReaded)
		if saved {
			break
		}
        bets = append(bets, bet)
        count++
    }

    if err := scanner.Err(); err != nil {
		log.Errorf("action: read_file | ressult: fail | error: %v", err)
        return true, 0, err
    }

	if len(bets) > 0 {
		err := c.socket.SendBatch(bets)
    	return !keepReading, count, err
	}
    return !keepReading, 0, nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(filename string) error {
    file, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer file.Close()

	err = c.createClientSocket()
	if err != nil {
        return err
    }
	scanner := bufio.NewScanner(file)
    for c.keep_running {
		finished, count, err := c.sendBatch(scanner)
        if err != nil || count == 0 {
            return err
        }
		log.Debugf("action: waiting_response | ammount_sent: %v", count)
		
		err = c.receiveMessage(count)
		
		if err != nil || finished {
			break
		}
    }
	log.Debugf("Loop finished")
	c.Close()
    return nil
}

func (c *Client) Close() {
	if !c.keep_running {
		return
	}
	log.Infof("action: shutdown | result: success | info: Client shutdown completed")
	c.socket.Close()
	c.keep_running = false
}
