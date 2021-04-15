// Code developed by the team member
// This file is used for control the virtual human
// It has socket module, game module,speech module, and animation control module
using CrazyMinnow.SALSA;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System;
using System.Threading;


public class VH : MonoBehaviour
{
    public Salsa salsa; // Salsa Plugin variable
    AudioSource adrSrc; // unity audiosource variable, used for loading audioclip
    Socket clientSocket; // client socket
    Animator animator;  // used to control animator
    byte[] buffer = new byte[1024]; // socket message buffer
    public static System.Random rd = new System.Random(); // random seed 
    public int power;	 	//random number for choosing VH hand esture during the game
    Queue instructionQueue; //stores the instruction sent from server
    Queue UserGameRecords;  //stores users records for 3 rounds	
    Queue VHgameQueue;      //stores VH hand gesture for displaying animations
    Queue VHGameRecords;    //stores VH records for 3 rounds
    int gameRound=0;		//game round counter
    int user=0,vh=0;        // winning round counter
    string[] VHHandGestures = {"rock", "paper", "scissor"};
    string Insevent; //socket message event
    string Instype; //socket message type
	
    // Start is called before the first frame update
    void Start()
    {
        salsa = (Salsa)GameObject.Find("biaoqing12").GetComponent<Salsa>();
        animator =  salsa.GetComponent<Animator>();
        instructionQueue = new Queue();
        UserGameRecords = new Queue();
        VHgameQueue = new Queue();
        VHGameRecords = new Queue();

		//start socket connection
        startClient(); 

        animator.speed = 2F;
    }

	// start client and connect to the python server
    void startClient(){
        Debug.Log("Start Client!");
        string serverIP = "127.0.0.1"; //use local host
        int port = 31500;
        clientSocket = new Socket(AddressFamily.InterNetwork,
        SocketType.Stream, ProtocolType.Tcp);
        clientSocket.Connect(new IPEndPoint(IPAddress.Parse(serverIP), port));
        // receive msg
        clientSocket.BeginReceive(buffer, 0, buffer.Length, SocketFlags.None, new AsyncCallback(ReceiveMessage), clientSocket);

    }

	//an asynchronous socket message module
    public void ReceiveMessage(IAsyncResult ar)
    {
        try
        {
            var socket = ar.AsyncState as Socket;
            var length = socket.EndReceive(ar);
            var message = Encoding.UTF8.GetString(buffer, 0, length);
            Debug.LogFormat("[Recevied] {0}",message);

			//split received message into type and specific event
            string[] sArray = message.Split('.');
            Insevent = sArray[1];
            Instype = sArray[0];
						
            if (string.Compare(Instype,"game") == 0){ // if the instruction type is game
                if (string.Compare(Insevent,"gameEnd") == 0){ //if the instruction event is gameEnd
                    // {gameStart}
                    instructionQueue.Enqueue(Insevent);		  //enqueue the event to be latter called in Update()
                }
                else if(string.Compare(Insevent,"gameStart") == 0){ //if the instruction event is gameStart
					instructionQueue.Enqueue(Insevent);		 //enqueue the event to be latter called in Update()
                    
					//initialize variables
					user = 0;	
					vh = 0;
                }
                else if (string.Compare(Insevent,"chooseGesture") == 0){ // if the instruction event is choooseGesture
                    //randomly choose a gesture from {rock,paper,scissor}
                    power = rd.Next(0, 3);
                    string selectedGesture = VHHandGestures[power];
					
					//enqueue the selected gesture both in gameQueue for displaying animaition
					//and in game records queue for calculating the results
                    VHgameQueue.Enqueue(selectedGesture);
                    VHGameRecords.Enqueue(selectedGesture);
                    Debug.LogFormat("[VH] {0}",selectedGesture);
                }
                else { 
                    UserGameRecords.Enqueue(Insevent); //stores users' every-round hand gesture 
                }
            }
			else if (string.Compare(Instype,"conv") == 0){
				instructionQueue.Enqueue(Insevent);

            }

            //receive next message, recursively listen for new message
            socket.BeginReceive(buffer, 0, buffer.Length, SocketFlags.None, new AsyncCallback(ReceiveMessage), socket);
        }
        catch(Exception ex)
        {
            Console.WriteLine(ex.Message);
        }
    }

	//load the audioClip to be displayed by the salsa lip-sync plugin
    void setAudioClip(string audioFile){
        var audSrc = salsa.GetComponent<AudioSource>();
        var audioClip =Resources.Load<AudioClip>(audioFile);
        if (audioClip == null){
            Debug.Log("failed to load.");
        }
        else
        {
            audSrc.clip = audioClip;
            audSrc.playOnAwake = true;
            audSrc.loop = false;
            salsa.audioSrc = audSrc;
            salsa.audioSrc.Play();
        }
    }
	
	//display the corresponding sentence required by the message
	void speak(string message){
		if (string.Compare(message,"gameEnd") == 0){
            if (user > vh){
                string audioFile = "Audio/wingame";
                setAudioClip(audioFile);
                Debug.Log("Congratulation, you win!");
            }				
            else if (user < vh){
                string audioFile = "Audio/losegame";
                setAudioClip(audioFile);
                Debug.Log("Come back to me next time, young kid.");
            }
            else if (user == vh){
                string audioFile = "Audio/tie";
                setAudioClip(audioFile);
                Debug.Log("It is a close match. You are as good as me");
            }
        }
		else if (string.Compare(message,"gameStart")==0 
				|| string.Compare(message,"name") == 0
				|| string.Compare(message,"countDown") ==0 ){
			string audioFile = "Audio/" + message;
			setAudioClip(audioFile);
		}			
		else{
			string audioFile = "Audio/" + message;
			animator.SetBool("hello",true);
			setAudioClip(audioFile);							
		}
	}
    // Update is called once per frame
    void Update()
    {
        if (instructionQueue.Count > 0){
            string message = (string) instructionQueue.Dequeue();
            speak(message);
        }

        if (VHgameQueue.Count > 0){ //if there are animation to be displayed
            if (animator.GetBool("rock") == false &&
                animator.GetBool("paper") == false &&
                animator.GetBool("scissor") == false ){ // if currently there are no animation is being played
                string selectedGesture = (string) VHgameQueue.Dequeue();
                animator.SetBool(selectedGesture, true); //play the selected aniamtion
                gameRound++;
            }
        }
        if (gameRound == 3 && UserGameRecords.Count == 3 ) { //if the game reaches round 3 and we have received three use gestures
            while (gameRound > 0){
                string VHHandGesture = (string)VHGameRecords.Dequeue();
                string UserHandGesture = (string) UserGameRecords.Dequeue();
				
				//calculate the results
                if (string.Compare(VHHandGesture, "rock") == 0){
                    if (string.Compare(UserHandGesture, "paper") == 0)
                        user++;
                    else if (string.Compare(UserHandGesture, "scissor") == 0)
                        vh++;
                }
                else if (string.Compare(VHHandGesture, "paper") == 0){
                    if (string.Compare(UserHandGesture, "scissor") == 0)
                        user++;
                    else if (string.Compare(UserHandGesture, "rock")==0)
                        vh++;
                }
                else if (string.Compare(VHHandGesture, "scissor") == 0){
                    if (string.Compare(UserHandGesture, "rock") == 0)
                        user++;
                    else if (string.Compare(UserHandGesture, "paper") == 0)
                        vh++;
                }
                gameRound--;
            }

        }
    }
}
